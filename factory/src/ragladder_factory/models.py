from typing import Any, Literal
from pydantic import BaseModel

class Chunk(BaseModel):
    id: str
    text: str
    source: str
    metadata: dict[str, Any]

class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    x: float | None = None
    y: float | None = None

class GraphEdge(BaseModel):
    src: str
    dst: str
    relation: str

class Community(BaseModel):
    id: str
    label: str
    members: list[str]

class Hit(BaseModel):
    id: str
    score: float
    text: str

class Meta(BaseModel):
    id: str
    license: str | None
    version: str | None
    dep_count: int

class Step(BaseModel):
    kind: Literal["thought", "decompose", "tool_call", "grade", "final"]
    text: str
    tool: str | None = None
    tool_input: dict[str, Any] | None = None
    touched_ids: list[str] = []
    grade: Literal["pass", "fail"] | None = None

class Trace(BaseModel):
    question: str
    mode: Literal["vanilla", "graph", "agentic"]
    steps: list[Step]
    answer: str
    citations: list[str]
    generated_with: str