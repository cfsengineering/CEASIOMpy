"""
Lightweight assistant utilities for the Streamlit UI.

This is intentionally dependency-light and offline-friendly. It can be extended
with an LLM later, but provides basic code/result awareness out of the box.
"""

from __future__ import annotations

import csv
import re
from collections import deque
import os
import json
import urllib.request
import urllib.error
import shutil
import subprocess
import time
from pathlib import Path
from typing import Iterable

from ceasiompy.utils.commonpaths import get_wkdir
from ceasiompy.utils.ceasiompyutils import workflow_number
from rag import RagChunk, index_exists, search_index


_MAX_TEXT_CHARS = 20000
_RAG_MAX_RESULTS = 2
_RAG_MAX_CHARS = 600
_OLLAMA_NUM_PREDICT = 256
_OLLAMA_NUM_CTX = 2048


def get_assistant_response(prompt: str) -> str:
    """Generate a response using lightweight heuristics and local context."""

    prompt_l = prompt.lower().strip()

    rag_chunks = search_index(prompt, max_results=_RAG_MAX_RESULTS) if index_exists() else []
    rag_chunks = _filter_chunks_for_query(prompt, rag_chunks)
    specs_settings = _extract_settings_from_specs(rag_chunks)
    results_summary = _summarize_latest_results() if _looks_like_cfd_question(prompt_l) else ""

    if not _ollama_available():
        if not _ensure_ollama_ready():
            return (
                "Ollama is not available. Ensure the Ollama server is running and the "
                f"model '{_ollama_model()}' is pulled."
            )

    return _ollama_answer(prompt, rag_chunks, results_summary, specs_settings)


def _ollama_available() -> bool:
    return _ollama_model_exists(_ollama_model())


def _ollama_model() -> str:
    return os.environ.get("OLLAMA_MODEL", "phi3").strip()


def _ollama_model_exists(model: str) -> bool:
    if not model:
        return False
    req = urllib.request.Request(
        "http://localhost:11434/api/tags",
        headers={"Content-Type": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            body = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError):
        return False
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return False
    models = parsed.get("models", [])
    return any((item.get("name") or "").startswith(model) for item in models)


def _ensure_ollama_ready() -> bool:
    """Best-effort start + pull model if Ollama is installed."""
    if not shutil.which("ollama"):
        return False

    model = _ollama_model()

    if not _ollama_server_alive():
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            time.sleep(0.8)
        except Exception:
            return False

    if _ollama_model_exists(model):
        return True

    try:
        subprocess.run(
            ["ollama", "pull", model],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return False

    return _ollama_model_exists(model)


def _ollama_server_alive() -> bool:
    req = urllib.request.Request(
        "http://localhost:11434/api/tags",
        headers={"Content-Type": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=1) as resp:
            return bool(resp.read())
    except (urllib.error.URLError, TimeoutError):
        return False


def _ollama_answer(
    prompt: str,
    chunks: list["RagChunk"],
    results_summary: str,
    specs_settings: list[str],
) -> str:
    model = _ollama_model()
    if not model:
        return "Ollama: model name is empty."

    context_lines = []
    if chunks:
        context_lines.append("Repository snippets:")
        for chunk in chunks:
            snippet = chunk.text.strip()
            if len(snippet) > _RAG_MAX_CHARS:
                snippet = snippet[:_RAG_MAX_CHARS] + "..."
            context_lines.append(f"[{chunk.path}:{chunk.start_line}]")
            context_lines.append(snippet)

    if specs_settings:
        context_lines.append("Module settings (parsed from __specs__.py):")
        context_lines.extend(specs_settings)

    if results_summary:
        context_lines.append("Results summary:")
        context_lines.append(results_summary)

    prompt_text = _build_llm_prompt(prompt, "\n".join(context_lines))
    answer = _call_ollama(model, prompt_text)
    if not answer:
        return "Ollama: no response (is the server running?)."

    sources = _format_sources(chunks)
    if sources:
        return f"{answer}\n\nSources:\n{sources}"
    return answer


def _build_llm_prompt(question: str, context: str) -> str:
    return (
        "You are a CEASIOMpy assistant. Answer clearly and concisely. "
        "If the context contains the answer, use it and do not claim it is missing. "
        "If the context is irrelevant, say you need more info.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n"
        "Answer:"
    )


def _call_ollama(model: str, prompt: str) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": _OLLAMA_NUM_PREDICT,
            "num_ctx": _OLLAMA_NUM_CTX,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError):
        return ""

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return ""
    return parsed.get("response", "").strip()


def _format_sources(chunks: list["RagChunk"]) -> str:
    if not chunks:
        return ""
    lines = []
    for chunk in chunks:
        lines.append(f"- {_format_source_link(chunk.path, chunk.start_line)}")
    return "\n".join(lines)


def _filter_chunks_for_query(prompt: str, chunks: list["RagChunk"]) -> list["RagChunk"]:
    prompt_l = prompt.lower()
    module_tokens = ["pyavl", "su2run", "cpacs2gmsh", "smtrain", "staticstability"]
    if "avl" in prompt_l and "pyavl" not in prompt_l:
        prompt_l = prompt_l.replace("avl", "pyavl")

    wants_settings = "settings" in prompt_l or "gui" in prompt_l
    wants_meshing = "mesh" in prompt_l or "meshing" in prompt_l

    for token in module_tokens:
        if token in prompt_l:
            filtered = [chunk for chunk in chunks if token in chunk.path.lower()]
            if wants_settings:
                specs_only = [chunk for chunk in filtered if "__specs__.py" in chunk.path]
                if specs_only:
                    return specs_only
            if wants_meshing and token == "pyavl":
                mesh_chunks = [chunk for chunk in chunks if "cpacs2gmsh" in chunk.path.lower()]
                return mesh_chunks or filtered or chunks
            return filtered or chunks
    return chunks


def _format_source_link(path: str, start_line: int) -> str:
    base_url = "https://github.com/cfsengineering/CEASIOMpy/blob/main/"
    return f"{base_url}{path}#L{start_line}"


def _extract_settings_from_specs(chunks: list["RagChunk"]) -> list[str]:
    settings: list[str] = []
    for chunk in chunks:
        if "__specs__.py" not in chunk.path:
            continue
        name = default = desc = None
        for line in chunk.text.splitlines():
            stripped = line.strip()
            if stripped.startswith("name="):
                name = _extract_quoted_value(stripped)
            elif stripped.startswith("default_value="):
                default = stripped.split("=", 1)[1].strip().rstrip(",")
            elif stripped.startswith("description="):
                desc = _extract_quoted_value(stripped)

            if name and (default or desc):
                parts = [name]
                if default:
                    parts.append(f"default={default}")
                if desc:
                    parts.append(desc)
                settings.append("- " + " | ".join(parts))
                name = default = desc = None
    return settings


def _extract_quoted_value(text: str) -> str | None:
    if "\"" in text:
        return text.split("\"", 1)[1].rsplit("\"", 1)[0]
    return None


def _looks_like_cfd_question(prompt_l: str) -> bool:
    keywords = [
        "cfd",
        "su2",
        "avl",
        "results",
        "lift",
        "drag",
        "cl",
        "cd",
        "cm",
        "aero",
        "pressure",
    ]
    return any(key in prompt_l for key in keywords)


def _summarize_latest_results() -> str:
    wkdir = get_wkdir()
    if not wkdir.exists():
        return "Results summary: WKDIR does not exist."

    workflow_dir = _latest_workflow_dir(wkdir)
    if workflow_dir is None:
        return "Results summary: no workflows found in WKDIR."

    results_dir = workflow_dir / "Results"
    if not results_dir.exists():
        return f"Results summary: {workflow_dir.name} has no Results folder."

    module_dirs = [d for d in results_dir.iterdir() if d.is_dir()]
    module_names = sorted(d.name for d in module_dirs)
    summary_lines = [
        f"Results summary (latest workflow: {workflow_dir.name}):",
        f"- Modules: {', '.join(module_names) if module_names else 'none'}",
    ]

    su2_log = _find_first(results_dir.rglob("logfile_SU2_CFD.log"))
    if su2_log:
        coeffs = _parse_su2_coefficients(su2_log)
        if coeffs:
            summary_lines.append("- SU2 coefficients: " + ", ".join(coeffs))

    csv_insights = _extract_csv_metrics(results_dir)
    if csv_insights:
        summary_lines.append("- CSV metrics: " + "; ".join(csv_insights))

    return "\n".join(summary_lines)


def _latest_workflow_dir(wkdir: Path) -> Path | None:
    workflow_dirs = [
        wkflow
        for wkflow in wkdir.iterdir()
        if wkflow.is_dir() and wkflow.name.startswith("Workflow_")
    ]
    if not workflow_dirs:
        return None
    return max(workflow_dirs, key=workflow_number)


def _find_first(paths: Iterable[Path]) -> Path | None:
    for path in paths:
        return path
    return None


def _parse_su2_coefficients(log_path: Path) -> list[str]:
    try:
        text = log_path.read_text(errors="replace")
    except OSError:
        return []

    if len(text) > _MAX_TEXT_CHARS:
        text = text[-_MAX_TEXT_CHARS:]

    coeffs: list[str] = []
    for name in ["CL", "CD", "CMz", "CMx", "CMy"]:
        value = _extract_last_value(text, name)
        if value is not None:
            coeffs.append(f"{name}={value}")
    return coeffs


def _extract_last_value(text: str, key: str) -> str | None:
    pattern = rf"\b{re.escape(key)}\b\s*[:=]\s*([-+0-9.eE]+)"
    matches = re.findall(pattern, text)
    if not matches:
        return None
    return matches[-1]


def _extract_csv_metrics(results_dir: Path) -> list[str]:
    metrics: list[str] = []
    for path in results_dir.rglob("*.csv"):
        insight = _summarize_csv(path)
        if insight:
            metrics.append(insight)
        if len(metrics) >= 3:
            break
    return metrics


def _summarize_csv(path: Path) -> str | None:
    try:
        with path.open(newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
            if not header:
                return None
            wanted = ["CL", "CD", "CM", "Lift", "Drag"]
            indices = {name: idx for idx, name in enumerate(header) if name in wanted}
            if not indices:
                return None
            last_row = None
            buffer = deque(reader, maxlen=1)
            if buffer:
                last_row = buffer[0]
            if not last_row:
                return None
            parts = []
            for name, idx in indices.items():
                if idx < len(last_row):
                    parts.append(f"{name}={last_row[idx]}")
            if not parts:
                return None
            return f"{path.name}: " + ", ".join(parts)
    except OSError:
        return None
    except csv.Error:
        return None
