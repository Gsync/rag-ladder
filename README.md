# The RAG Ladder

An interactive explainer for **Vanilla, Graph, and Agentic RAG** — taught on a real
npm dependency graph instead of toy data. Ask a question, watch each retrieval
strategy work through it, and see exactly where the simpler ones fall short.

No API key needed and no LLM calls happen live. All the interesting parts —
embeddings, graph layout, agent traces — are precomputed offline and shipped as
static JSON. The site only re-embeds *your* query in-browser to run a live
cosine search against the precomputed vectors.

## Quickstart

You don't need Python or an LLM to run the site — the data artifacts are
already committed to the repo.

```sh
pnpm -C app install
pnpm dev
```

Open the printed local URL and start asking questions.

## How it's built

Two halves:

- **`factory/`** — a Python CLI that crawls npm/deps.dev data for a small set
  of seed packages, embeds and chunks it, builds a dependency graph with
  community detection, and (optionally, using a local Ollama model) generates
  offline agent traces. Its output lands in `datasets/npm/` as small committed
  JSON/`.npy` files.
- **`app/`** — a static SvelteKit site that loads those artifacts and renders
  the interactive scatter plots, graph explorer, and agent trace viewer.

You only need the factory if you want to regenerate the data yourself (e.g.
with a different set of packages):

```sh
cd factory
uv sync
uv run factory crawl --ecosystem npm --seeds seeds.txt   # fetch + cache raw data
uv run factory build                                      # chunk + embed + project
uv run factory graph                                      # build graph + communities
uv run factory traces                                     # generate agent traces (needs Ollama)
uv run factory grounding                                  # generate the grounding demo (needs Ollama)
```

## Status

Vanilla RAG (embedding playground, chunking lab, grounding demo) is built.
Graph and Agentic RAG modules are in progress.

## License

Code is MIT-licensed (see `LICENSE`). Crawled data sources and their licenses
are listed in `DATA_LICENSES.md`.
