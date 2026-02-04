"""Local, offline RAG index utilities."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import pdfplumber
except Exception:  # pragma: no cover - optional dependency
    pdfplumber = None

_INDEX_PATH = Path(__file__).parent / "rag_index" / "index.json"


@dataclass(frozen=True)
class RagChunk:
    path: str
    start_line: int
    end_line: int
    text: str


def index_exists() -> bool:
    return _INDEX_PATH.exists()


def load_index() -> dict:
    if not _INDEX_PATH.exists():
        return {"chunks": []}
    return json.loads(_INDEX_PATH.read_text(encoding="utf-8"))


def search_index(query: str, *, max_results: int = 5) -> list[RagChunk]:
    data = load_index()
    chunks = data.get("chunks", [])
    if not chunks:
        return []

    tokens = _tokenize(query)
    if not tokens:
        return []

    scored: list[tuple[int, dict]] = []
    for chunk in chunks:
        text_l = chunk.get("text", "").lower()
        path_l = chunk.get("path", "").lower()
        score = sum(text_l.count(token) for token in tokens)

        # Boost matches when query tokens appear in the file path (module names, folders).
        path_bonus = 0
        for token in tokens:
            if token in path_l:
                path_bonus += 5
        score += path_bonus
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)

    results: list[RagChunk] = []
    for _, chunk in scored[:max_results]:
        results.append(
            RagChunk(
                path=chunk.get("path", ""),
                start_line=chunk.get("start_line", 1),
                end_line=chunk.get("end_line", 1),
                text=chunk.get("text", ""),
            )
        )
    return results


def build_index(
    repo_root: Path,
    *,
    out_path: Path | None = None,
    include_exts: Iterable[str] | None = None,
    include_only_knowledge: bool = False,
    chunk_lines: int = 60,
) -> Path:
    if out_path is None:
        out_path = _INDEX_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if include_exts is None:
        include_exts = [
            ".py",
            ".md",
            ".txt",
            ".yml",
            ".yaml",
            ".toml",
            ".ini",
            ".cfg",
            ".pdf",
        ]

    chunks: list[dict] = []
    excluded_dirs = {
        ".git",
        "WKDIR",
        "INSTALLDIR",
        "test_files",
        "test_cases",
        "tests",
        "documents",
        "__pycache__",
    }
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in include_exts:
            continue
        if any(part.startswith(".") for part in path.parts):
            continue
        if any(part in excluded_dirs for part in path.parts):
            continue
        if include_only_knowledge and not _is_knowledge_file(path):
            continue
        lines = _read_file_lines(path)
        if lines is None:
            continue

        for idx in range(0, len(lines), chunk_lines):
            chunk = lines[idx : idx + chunk_lines]
            if not chunk:
                continue
            chunks.append(
                {
                    "path": str(path.relative_to(repo_root)),
                    "start_line": idx + 1,
                    "end_line": idx + len(chunk),
                    "text": "\n".join(chunk),
                }
            )

    payload = {
        "version": 1,
        "chunk_lines": chunk_lines,
        "chunks": chunks,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def _is_knowledge_file(path: Path) -> bool:
    name = path.name.lower()
    if name == "readme.md":
        return True
    if name == "__specs__.py":
        return True
    if name.endswith(".pdf"):
        return True
    return False


def _tokenize(text: str) -> list[str]:
    return [token for token in re.split(r"\W+", text.lower()) if token]


def _read_file_lines(path: Path) -> list[str] | None:
    if path.suffix.lower() == ".pdf":
        if pdfplumber is None:
            return None
        try:
            text_parts: list[str] = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    if text:
                        text_parts.append(text)
            return "\n".join(text_parts).splitlines()
        except Exception:
            return None

    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
