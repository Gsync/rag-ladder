import asyncio
from pathlib import Path

import typer
from dotenv import load_dotenv

from ragladder_factory.crawl import crawl as run_crawl

from ragladder_factory.build import build as run_build
from ragladder_factory.graph import graph as run_graph

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


if __name__ == "__main__":
    app()
