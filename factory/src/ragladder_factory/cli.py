import typer

app = typer.Typer(help="RAG Ladder data factory")

@app.command()
def hello() -> None:
   """Sanity check."""
   print("factory is alive")

@app.command()
def version() -> None:
   """Print factory version."""
   print("0.1.0")

if __name__ == "__main__":
   app()