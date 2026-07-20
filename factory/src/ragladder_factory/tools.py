from __future__ import annotations

import json
from pathlib import Path

import networkx as nx
import numpy as np
from fastembed import TextEmbedding

from ragladder_factory.models import Chunk, Community, GraphNode, Hit, Meta


def _to_id(name: str) -> str:
    return name if name.startswith("npm:") else f"npm:{name}"


class Toolset:
    """Loads all committed artifacts once and exposes the 6 typed agent tools."""

    def __init__(self, out_dir: Path) -> None:
        self.chunks = [Chunk(**d) for d in json.loads((out_dir / "chunks.json").read_text())]
        self.chunks_by_id = {c.id: c for c in self.chunks}
        self.embeddings = np.load(out_dir / "embeddings.npy")

        graph_data = json.loads((out_dir / "graph.json").read_text())
        nodes = [GraphNode(**d) for d in graph_data["nodes"]]
        self.label_by_id = {n.id: n.label for n in nodes}
        self.G: nx.DiGraph[str] = nx.DiGraph()
        self.G.add_nodes_from(n.id for n in nodes)
        self.G.add_edges_from((e["src"], e["dst"]) for e in graph_data["edges"])

        self.communities = [Community(**d) for d in json.loads((out_dir / "communities.json").read_text())]

        self._embedder = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")

    def vector_search(self, query: str, k: int = 5) -> tuple[list[Hit], list[str]]:
        qvec = np.array(list(self._embedder.embed([query])), dtype="float32")[0]
        norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(qvec)
        scores = (self.embeddings @ qvec) / norms
        top = np.argsort(-scores)[:k]
        hits = [Hit(id=self.chunks[i].id, score=float(scores[i]), text=self.chunks[i].text) for i in top]
        return hits, [h.id for h in hits]

    def find_package(self, name: str) -> tuple[Chunk | None, list[str]]:
        chunk = self.chunks_by_id.get(_to_id(name))
        if chunk is None:
            return None, []
        return chunk, [chunk.id]

    def get_dependencies(self, name: str, transitive: bool = False) -> tuple[list[str], list[str]]:
        node_id = _to_id(name)
        if node_id not in self.G:
            return [], []
        dep_ids = sorted(nx.descendants(self.G, node_id) if transitive else self.G.successors(node_id))
        names = [self.label_by_id[d] for d in dep_ids]
        return names, [node_id, *dep_ids]

    def get_dependents(self, name: str, transitive: bool = False) -> tuple[list[str], list[str]]:
        node_id = _to_id(name)
        if node_id not in self.G:
            return [], []
        dep_ids = sorted(nx.ancestors(self.G, node_id) if transitive else self.G.predecessors(node_id))
        names = [self.label_by_id[d] for d in dep_ids]
        return names, [node_id, *dep_ids]

    def get_package_meta(self, name: str) -> tuple[Meta | None, list[str]]:
        node_id = _to_id(name)
        chunk = self.chunks_by_id.get(node_id)
        if chunk is None:
            return None, []
        dep_count = self.G.out_degree(node_id) if node_id in self.G else 0
        meta = Meta(
            id=node_id,
            license=chunk.metadata.get("license"),
            version=chunk.metadata.get("version"),
            dep_count=dep_count,
        )
        return meta, [node_id]

    def list_communities(self) -> tuple[list[Community], list[str]]:
        touched = [m for c in self.communities for m in c.members]
        return self.communities, touched
