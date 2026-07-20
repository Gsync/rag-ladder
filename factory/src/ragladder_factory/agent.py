from __future__ import annotations

import json
from typing import Any, Literal

import instructor
from pydantic import BaseModel

from ragladder_factory.models import Step
from ragladder_factory.tools import Toolset

TOOL_DESCRIPTIONS: dict[str, str] = {
    "vector_search": "vector_search(query: str, k: int = 5) -> top-k {id, score, text} by cosine similarity",
    "find_package": "find_package(name: str) -> exact package lookup {id, text, source, metadata} or null",
    "get_dependencies": "get_dependencies(name: str, transitive: bool = False) -> package names this package depends on",
    "get_dependents": "get_dependents(name: str, transitive: bool = False) -> package names that depend on this package",
    "get_package_meta": "get_package_meta(name: str) -> {license, version, dep_count} or null",
    "list_communities": "list_communities() -> all {id, label, members} sub-ecosystem groups",
}

MODE_TOOLS: dict[str, list[str]] = {
    "vanilla": ["vector_search", "find_package"],
    "graph": ["find_package", "get_dependencies", "get_dependents", "get_package_meta", "list_communities"],
    "agentic": list(TOOL_DESCRIPTIONS.keys()),
}

CONTROLLER_PROMPT = """You answer questions about software packages using tools.
Tools:
{tools}

Think step by step. Reply as JSON:
{{"thought": str, "action": str, "action_input": dict}} to call a tool, OR
{{"thought": str, "final_answer": str, "citations": [str]}} to finish.
Cite package ids (e.g. "npm:debug") you relied on."""

DECOMPOSER_PROMPT = """Break this request into the minimal set of independent sub-questions
needed to answer it. Reply JSON: {"subquestions": [...]}."""

GRADER_PROMPT = """Given SUBQUESTION and RETRIEVED evidence, is the evidence sufficient
and relevant? Reply JSON: {"sufficient": bool, "reason": str, "refined_query": str|null}."""

SYNTHESIZER_PROMPT = """Given the sub-questions and their graded evidence, write the final
answer. Cite package ids you used. Be direct."""


class ControllerAction(BaseModel):
    thought: str
    action: str | None = None
    action_input: dict[str, Any] | None = None
    final_answer: str | None = None
    citations: list[str] = []


class DecomposerOutput(BaseModel):
    subquestions: list[str]


class GradeResult(BaseModel):
    sufficient: bool
    reason: str
    refined_query: str | None = None


class SynthesizerOutput(BaseModel):
    answer: str
    citations: list[str]


def serialize_observation(data: object) -> str:
    if data is None:
        return "null"
    if isinstance(data, list):
        return json.dumps([item.model_dump() if isinstance(item, BaseModel) else item for item in data])
    if isinstance(data, BaseModel):
        return json.dumps(data.model_dump())
    return json.dumps(data)


def call_tool(toolset: Toolset, name: str, tool_input: dict[str, Any]) -> tuple[object, list[str]]:
    method = getattr(toolset, name)
    result: tuple[object, list[str]] = method(**tool_input)
    return result


def run_react(
    client: instructor.Instructor,
    model: str,
    question: str,
    toolset: Toolset,
    tool_names: list[str],
    max_iters: int = 6,
) -> tuple[list[Step], str, list[str]]:
    tools_desc = "\n".join(f"- {TOOL_DESCRIPTIONS[t]}" for t in tool_names)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": CONTROLLER_PROMPT.format(tools=tools_desc)},
        {"role": "user", "content": question},
    ]
    steps: list[Step] = []

    for _ in range(max_iters):
        action = client.chat.completions.create(
            model=model,
            response_model=ControllerAction,
            temperature=0,
            messages=messages,  # type: ignore[arg-type]
        )
        if action.final_answer is not None:
            steps.append(Step(kind="final", text=action.final_answer))
            return steps, action.final_answer, action.citations

        steps.append(Step(kind="thought", text=action.thought))
        if action.action is None or action.action not in tool_names:
            break

        result, touched = call_tool(toolset, action.action, action.action_input or {})
        obs = serialize_observation(result)
        steps.append(
            Step(
                kind="tool_call",
                text=f"Called {action.action}({action.action_input or {}})",
                tool=action.action,
                tool_input=action.action_input,
                touched_ids=touched,
            )
        )
        messages.append({"role": "assistant", "content": action.model_dump_json()})
        messages.append({"role": "user", "content": f"Observation: {obs}"})

    fallback = "Unable to reach a final answer within the iteration budget."
    steps.append(Step(kind="final", text=fallback))
    return steps, fallback, []


def run_plan_execute_grade(
    client: instructor.Instructor,
    model: str,
    question: str,
    toolset: Toolset,
    max_react_iters: int = 6,
    max_grade_attempts: int = 3,
) -> tuple[list[Step], str, list[str]]:
    decomposed = client.chat.completions.create(
        model=model,
        response_model=DecomposerOutput,
        temperature=0,
        messages=[
            {"role": "system", "content": DECOMPOSER_PROMPT},
            {"role": "user", "content": question},
        ],
    )
    steps: list[Step] = [
        Step(
            kind="decompose",
            text=f"Decomposed into {len(decomposed.subquestions)} sub-questions",
            tool_input={"subquestions": decomposed.subquestions},
        )
    ]

    sub_answers: list[tuple[str, str]] = []
    citations: list[str] = []
    all_tools = list(TOOL_DESCRIPTIONS.keys())

    for subq in decomposed.subquestions:
        current_query = subq
        attempt = 0
        while True:
            sub_steps, sub_answer, sub_citations = run_react(
                client, model, current_query, toolset, all_tools, max_react_iters
            )
            steps.extend(sub_steps)
            grade = client.chat.completions.create(
                model=model,
                response_model=GradeResult,
                temperature=0,
                messages=[
                    {"role": "system", "content": GRADER_PROMPT},
                    {"role": "user", "content": f"SUBQUESTION: {subq}\nRETRIEVED: {sub_answer}"},
                ],
            )
            steps.append(
                Step(kind="grade", text=grade.reason, grade="pass" if grade.sufficient else "fail")
            )
            attempt += 1
            if grade.sufficient or attempt >= max_grade_attempts:
                sub_answers.append((subq, sub_answer))
                citations.extend(sub_citations)
                break
            current_query = grade.refined_query or current_query

    evidence = "\n".join(f"Q: {q}\nA: {a}" for q, a in sub_answers)
    synth = client.chat.completions.create(
        model=model,
        response_model=SynthesizerOutput,
        temperature=0,
        messages=[
            {"role": "system", "content": SYNTHESIZER_PROMPT},
            {"role": "user", "content": f"Original question: {question}\n\n{evidence}"},
        ],
    )
    steps.append(Step(kind="final", text=synth.answer))
    return steps, synth.answer, synth.citations


def run_agent(
    client: instructor.Instructor,
    model: str,
    question: str,
    mode: Literal["vanilla", "graph", "agentic"],
    toolset: Toolset,
    planning: bool = False,
) -> tuple[list[Step], str, list[str]]:
    tool_names = MODE_TOOLS[mode]
    if mode == "agentic" and planning:
        return run_plan_execute_grade(client, model, question, toolset)
    return run_react(client, model, question, toolset, tool_names)
