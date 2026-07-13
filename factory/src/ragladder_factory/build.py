import json
from pathlib import Path
from typing import cast

import numpy as np
import umap
from fastembed import TextEmbedding

from ragladder_factory.models import Chunk

def load_chunks(raw_dir: Path) -> list[Chunk]:
    chunks = []
    for path in sorted(raw_dir.glob("*__registry.json")):
        data = json.loads(path.read_text())
        name: str = data["name"]

        text = data.get("description") or ""
        keywords = data.get("keywords")
        if keywords:
            text += " Keywords: " + ", ".join(keywords)
        text = text.strip() or name

        chunks.append(
            Chunk(
                id=f"npm:{name}",
                text=text,
                source=f"https://registry.npmjs.org/{name}",
                metadata={
                    "ecosystem": "npm",
                    "license": data.get("license"),
                    "version": data.get("dist-tags", {}).get("latest"),
                }
            )
        )
    return chunks

def write_chunks(chunks: list[Chunk], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps([c.model_dump() for c in chunks], indent=2))

def embed_chunks(chunks: list[Chunk]) -> np.ndarray:
    model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    return np.array(list(model.embed([c.text for c in chunks])), dtype="float32")

def project_2d(vectors: np.ndarray) -> np.ndarray:
    reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, random_state=42)
    return cast(np.ndarray, reducer.fit_transform(vectors))

def write_projection(chunks: list[Chunk], xy: np.ndarray, out_path: Path) -> None:
    data = [{"id": c.id, "x": float(x), "y": float(y)} for c, (x, y) in zip(chunks, xy)]
    out_path.write_text(json.dumps(data, indent=2))

def write_readmes(readmes_dir: Path, out_path: Path) -> None:
    data = {f"npm:{path.stem}": path.read_text() for path in sorted(readmes_dir.glob("*.md"))}
    out_path.write_text(json.dumps(data, indent=2))

def build(raw_dir: Path, out_dir: Path) -> None:
    chunks = load_chunks(raw_dir)
    write_chunks(chunks, out_dir / "chunks.json")
    vectors = embed_chunks(chunks)
    np.save(out_dir / "embeddings.npy", vectors)
    xy = project_2d(vectors)
    write_projection(chunks, xy, out_dir / "projection.json")
    write_readmes(out_dir / "readmes", out_dir / "readmes.json")