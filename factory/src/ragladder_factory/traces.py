from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ragladder_factory.agent import run_agent
from ragladder_factory.llm import get_llm
from ragladder_factory.models import Trace
from ragladder_factory.tools import Toolset

QUESTIONS = [
    "a good date-handling library?",
    "what breaks if debug disappears?",
    "what are the major sub-ecosystems here?",
    "recommend a Node REST stack, then check each option's dependency count and license.",
]

MODES: list[str] = ["vanilla", "graph", "agentic"]


def build_demos(toolset: Toolset) -> list[Trace]:
    client, model = get_llm()
    generated_with = f"{model} @ {date.today().isoformat()}"

    demo_traces: list[Trace] = []
    for question in QUESTIONS:
        for mode in MODES:
            planning = mode == "agentic" and question == QUESTIONS[3]
            steps, answer, citations = run_agent(
                client, model, question, mode, toolset, planning=planning  # type: ignore[arg-type]
            )
            demo_traces.append(
                Trace(
                    question=question,
                    mode=mode,  # type: ignore[arg-type]
                    steps=steps,
                    answer=answer,
                    citations=citations,
                    generated_with=generated_with,
                )
            )
    return demo_traces


def write_demos(demo_traces: list[Trace], out_path: Path) -> None:
    out_path.write_text(json.dumps([t.model_dump() for t in demo_traces], indent=2))


def traces(out_dir: Path) -> None:
    toolset = Toolset(out_dir)
    demo_traces = build_demos(toolset)
    write_demos(demo_traces, out_dir / "demos.json")
