from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding
from pydantic import BaseModel

from ragladder_factory.llm import get_llm
from ragladder_factory.models import GroundingDemo, RetrievedChunk

FEATURE_PACKAGE = "npm:debug"
QUESTION = "how do I add a custom formatter to debug's output?"
# Deliberately smaller than M2's slider default (600/80): at this size the window
# boundary aligns with the "### Custom formatters" heading, so the real answer
# section actually wins retrieval (rank 5 at 600/80, rank 0 here) instead of the
# grounded answer honestly reporting "not in context".
CHUNK_SIZE = 300
CHUNK_OVERLAP = 40
TOP_K = 3

NO_CONTEXT_PROMPT = """Answer the user's question from your own general knowledge only.
No documentation has been provided to you. If you're not certain, say so rather than
inventing specifics."""

GROUNDED_PROMPT = """Answer the user's question using ONLY the CONTEXT chunks below —
do not use outside knowledge. Each chunk is labeled with an id. Cite the id(s) of the
chunk(s) you actually relied on in `citations`.

CONTEXT:
{context}"""


class NoContextAnswer(BaseModel):
    answer: str


class GroundedAnswer(BaseModel):
    answer: str
    citations: list[int]


def chunk_text(text: str, size: int, overlap: int) -> list[tuple[int, int, str]]:
    """Character-windowed chunking. Must match app/src/lib/chunker.ts exactly so
    a chunk's `start` id lines up between the factory and the browser."""
    step = max(1, size - overlap)
    chunks: list[tuple[int, int, str]] = []
    for start in range(0, len(text), step):
        end = min(start + size, len(text))
        chunks.append((start, end, text[start:end]))
        if end == len(text):
            break
    return chunks


def retrieve_top_chunks(readme: str, query: str, k: int) -> list[RetrievedChunk]:
    windows = chunk_text(readme, CHUNK_SIZE, CHUNK_OVERLAP)
    embedder = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    texts = [text for _, _, text in windows]
    vectors = np.array(list(embedder.embed(texts)), dtype="float32")
    qvec = np.array(list(embedder.embed([query])), dtype="float32")[0]
    norms = np.linalg.norm(vectors, axis=1) * np.linalg.norm(qvec)
    scores = (vectors @ qvec) / norms
    top = np.argsort(-scores)[:k]
    return [
        RetrievedChunk(start=windows[i][0], text=windows[i][2], score=float(scores[i])) for i in top
    ]


def build_grounding(readmes: dict[str, str]) -> GroundingDemo:
    readme = readmes[FEATURE_PACKAGE]
    chunks = retrieve_top_chunks(readme, QUESTION, TOP_K)

    client, model = get_llm()

    no_context = client.chat.completions.create(
        model=model,
        response_model=NoContextAnswer,
        temperature=0,
        messages=[
            {"role": "system", "content": NO_CONTEXT_PROMPT},
            {"role": "user", "content": QUESTION},
        ],
    )

    context = "\n\n".join(f"[chunk {c.start}]\n{c.text}" for c in chunks)
    grounded = client.chat.completions.create(
        model=model,
        response_model=GroundedAnswer,
        temperature=0,
        messages=[
            {"role": "system", "content": GROUNDED_PROMPT.format(context=context)},
            {"role": "user", "content": QUESTION},
        ],
    )

    return GroundingDemo(
        question=QUESTION,
        package_id=FEATURE_PACKAGE,
        chunks=chunks,
        no_context_answer=no_context.answer,
        grounded_answer=grounded.answer,
        citations=grounded.citations,
        generated_with=f"{model} @ {date.today().isoformat()}",
    )


def write_grounding(demo: GroundingDemo, out_path: Path) -> None:
    out_path.write_text(json.dumps(demo.model_dump(), indent=2))


def grounding(out_dir: Path) -> None:
    readmes: dict[str, str] = json.loads((out_dir / "readmes.json").read_text())
    demo = build_grounding(readmes)
    write_grounding(demo, out_dir / "grounding.json")
