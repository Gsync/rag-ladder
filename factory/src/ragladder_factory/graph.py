from __future__ import annotations

import json
from pathlib import Path

import networkx as nx

from ragladder_factory.models import Community, GraphEdge, GraphNode

def load_nodes(raw_dir: Path) -> list[GraphNode]:
    nodes = []
    for path in sorted(raw_dir.glob("*__registry.json")):
        data = json.loads(path.read_text())
        name: str = data["name"]
        nodes.append(GraphNode(id=f"npm:{name}", label=name, type="package"))
    return nodes

def load_edges(raw_dir: Path, node_ids: set[str]) -> list[GraphEdge]:
    seen: set[tuple[str, str]] = set()
    edges = []
    for path in sorted(raw_dir.glob("*__deps.json")):
        data = json.loads(path.read_text())
        names = [node["versionKey"]["name"] for node in data["nodes"]]
        for edge in data["edges"]:
            src = f"npm:{names[edge['fromNode']]}"
            dst = f"npm:{names[edge['toNode']]}"
            if src not in node_ids or dst not in node_ids:
                continue
            if (src, dst) in seen:
                continue
            seen.add((src, dst))
            edges.append(GraphEdge(src=src, dst=dst, relation="DEPENDS_ON"))
    return edges

def build_graph(nodes: list[GraphNode], edges: list[GraphEdge]) -> nx.DiGraph[str]:
    G: nx.DiGraph[str] = nx.DiGraph()
    G.add_nodes_from(n.id for n in nodes)
    G.add_edges_from((e.src, e.dst) for e in edges)
    return G

def apply_layout(nodes: list[GraphNode], G: nx.DiGraph[str]) -> None:
    pos = nx.spring_layout(G, seed=42)
    for node in nodes:
        node.x, node.y = map(float, pos[node.id])

def detect_communities(G: nx.DiGraph[str]) -> list[Community]:
    groups = nx.community.louvain_communities(G.to_undirected(), seed=42)
    return [
        Community(id=f"community:{i}", label=f"Community {i}", members=sorted(group))
        for i, group in enumerate(groups)
    ]

def write_graph(nodes: list[GraphNode], edges: list[GraphEdge], out_path: Path) -> None:
    data = {
        "nodes": [n.model_dump() for n in nodes],
        "edges": [e.model_dump() for e in edges],
    }
    out_path.write_text(json.dumps(data, indent=2))

def write_communities(communities: list[Community], out_path: Path) -> None:
    out_path.write_text(json.dumps([c.model_dump() for c in communities], indent=2))

def graph(raw_dir: Path, out_dir: Path) -> None:
    nodes = load_nodes(raw_dir)
    node_ids = {n.id for n in nodes}
    edges = load_edges(raw_dir, node_ids)
    G = build_graph(nodes, edges)
    apply_layout(nodes, G)
    communities = detect_communities(G)
    write_graph(nodes, edges, out_dir / "graph.json")
    write_communities(communities, out_dir / "communities.json")
