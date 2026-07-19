from typing import Any
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