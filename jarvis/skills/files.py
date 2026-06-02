"""File skills: search, open, read, and write notes — restricted to configured roots."""

from __future__ import annotations

from pathlib import Path

from ..context import get_context
from . import skill


def _within_roots(target: Path) -> bool:
    """True if target is inside one of the allowed file roots."""
    target = target.resolve()
    for root in get_context().config.resolved_file_roots():
        try:
            target.relative_to(root)
            return True
        except ValueError:
            continue
    return False


@skill(
    name="search_files",
    description="Search for files by name (glob pattern) under the allowed roots.",
    parameters={
        "pattern": {"type": "string", "description": "Glob, e.g. *.pdf or report*"},
        "limit": {"type": "integer", "description": "Max results (default 20)"},
    },
    group="files",
)
def search_files(pattern: str, limit: int = 20) -> str:
    results: list[str] = []
    for root in get_context().config.resolved_file_roots():
        for p in root.rglob(pattern):
            results.append(str(p))
            if len(results) >= limit:
                break
        if len(results) >= limit:
            break
    if not results:
        return f"No files matching '{pattern}'."
    return "Found:\n" + "\n".join(f"- {r}" for r in results)


@skill(
    name="read_file",
    description="Read and return the text contents of a file (first ~4000 chars).",
    parameters={"path": {"type": "string", "description": "Absolute file path"}},
    group="files",
)
def read_file(path: str) -> str:
    p = Path(path).expanduser()
    if not _within_roots(p):
        return "Access denied: file is outside the allowed roots."
    if not p.is_file():
        return f"No such file: {path}"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"Could not read file: {exc}"
    return text[:4000] + ("\n…(truncated)" if len(text) > 4000 else "")


@skill(
    name="open_file",
    description="Open a file with its default application.",
    parameters={"path": {"type": "string", "description": "Absolute file path"}},
    group="files",
)
def open_file(path: str) -> str:
    return get_context().adapter.open_app(str(Path(path).expanduser()))
