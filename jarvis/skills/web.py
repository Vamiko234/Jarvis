"""Web skills: open URLs, search the web, and fetch+extract a page's text."""

from __future__ import annotations

from ..context import get_context
from . import skill


@skill(
    name="open_url",
    description="Open a URL in the default web browser.",
    parameters={"url": {"type": "string", "description": "Full URL incl. https://"}},
    group="web",
)
def open_url(url: str) -> str:
    return get_context().adapter.open_app(url)


@skill(
    name="web_search",
    description="Search the web and return the top result titles, snippets, and links.",
    parameters={
        "query": {"type": "string", "description": "Search query"},
        "max_results": {"type": "integer", "description": "Number of results (default 5)"},
    },
    group="web",
)
def web_search(query: str, max_results: int = 5) -> str:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return "Web search unavailable: install duckduckgo-search."
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        return f"Search failed: {exc}"
    if not hits:
        return f"No results for '{query}'."
    lines = [f"- {h.get('title')}\n  {h.get('body', '')}\n  {h.get('href')}" for h in hits]
    return "Search results:\n" + "\n".join(lines)


@skill(
    name="fetch_page",
    description="Fetch a web page and return its readable text (first ~4000 chars).",
    parameters={"url": {"type": "string", "description": "Full URL to fetch"}},
    group="web",
)
def fetch_page(url: str) -> str:
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return "Page fetch unavailable: install requests and beautifulsoup4."
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Jarvis/0.1"})
        resp.raise_for_status()
    except Exception as exc:
        return f"Could not fetch page: {exc}"
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return text[:4000] + ("\n…(truncated)" if len(text) > 4000 else "")
