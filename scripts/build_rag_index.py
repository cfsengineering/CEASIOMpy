"""Build a local RAG index for the CEASIOMpy repo."""

# Futures
from __future__ import annotations

# Imports
import sys

from src.app.rag import build_index

from pathlib import Path


# Constants
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src" / "app"))


# Main
def main() -> int:
    out_path = build_index(repo_root, include_only_knowledge=True, chunk_lines=60)
    print(f"Wrote RAG index to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
