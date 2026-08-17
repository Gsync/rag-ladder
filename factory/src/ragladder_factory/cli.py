import asyncio
from pathlib import Path

import typer
from dotenv import load_dotenv

from ragladder_factory.crawl import crawl as run_crawl

from ragladder_factory.build import build as run_build
from ragladder_factory.graph import graph as run_graph
from ragladder_factory.grounding import grounding as run_grounding
from ragladder_factory.traces import traces as run_traces

load_dotenv()

app = typer.Typer(help="RAG Ladder data factory")


@app.command()
def hello() -> None:
    """Sanity check."""
    print("factory is alive")


@app.command()
def version() -> None:
    """Print factory version."""
    print("0.1.0")


@app.command()
def crawl(
    ecosystem: str = typer.Option("npm", help="Package ecosystem to crawl."),
    seeds: Path = typer.Option(..., help="Path to a text file of seed package names."),
) -> None:
    """Crawl dependency data and registry text for the seed packages."""
    raw_dir = Path(f"../datasets/{ecosystem}/raw")
    readmes_dir = Path(f"../datasets/{ecosystem}/readmes")
    asyncio.run(run_crawl(seeds, raw_dir, readmes_dir))


@app.command()
def build(
    ecosystem: str = typer.Option("npm", help="Package ecosystem to build."),
) -> None:
    """Build chunks.json from the crawled cache."""
    raw_dir = Path(f"../datasets/{ecosystem}/raw")
    out_dir = Path(f"../datasets/{ecosystem}")
    run_build(raw_dir, out_dir)


@app.command()
def graph(
    ecosystem: str = typer.Option("npm", help="Package ecosystem to build the graph for."),
) -> None:
    """Build graph.json and communities.json from the crawled cache."""
    raw_dir = Path(f"../datasets/{ecosystem}/raw")
    out_dir = Path(f"../datasets/{ecosystem}")
    run_graph(raw_dir, out_dir)


@app.command()
def traces(
    ecosystem: str = typer.Option("npm", help="Package ecosystem to generate traces for."),
) -> None:
    """Generate agent traces (demos.json). Needs a running LLM (Ollama/DeepSeek); never run in CI."""
    out_dir = Path(f"../datasets/{ecosystem}")
    run_traces(out_dir)


@app.command()
def grounding(
    ecosystem: str = typer.Option("npm", help="Package ecosystem to generate the grounding demo for."),
) -> None:
    """Generate the M3 grounding demo (grounding.json). Needs a running LLM; never run in CI."""
    out_dir = Path(f"../datasets/{ecosystem}")
    run_grounding(out_dir)


if __name__ == "__main__":
    app()
