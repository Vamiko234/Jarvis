"""Research agent: multi-source web research producing a cited markdown report.

Flow:
  1. Decompose topic into sub-questions (smart model)
  2. For each sub-question: web_search → fetch top pages → extract text
  3. Synthesize a cited markdown report (smart model)
  4. Save to ~/.jarvis/research/<slug>.md
  5. Return a 2-sentence spoken summary

Requires: duckduckgo-search, requests, beautifulsoup4 (all in requirements.txt)
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any


_PLAN_SYSTEM = (
    "You are a research planner. Given a topic, output a JSON array of 3-5 "
    "focused sub-questions that together give full coverage of the topic. "
    "Return ONLY a JSON array of strings. Example: "
    '["What is X?", "How does X work?", "What are the tradeoffs of X?"]'
)

_SYNTH_SYSTEM = (
    "You are a research analyst. Synthesize the sources below into a concise "
    "markdown report. Include:\n"
    "## Summary\n- 3-4 bullet points of the key takeaways\n\n"
    "## Findings\nDetailed findings with inline citations [1], [2], etc.\n\n"
    "## Sources\nNumbered list: [N] URL\n\n"
    "Be specific. Use real data and facts from the sources. "
    "Do not pad with generic filler."
)

_SPOKEN_SYSTEM = (
    "Summarize the following research report in exactly 2 sentences suitable "
    "for reading aloud. No markdown, no lists, plain prose."
)


class ResearchAgent:
    def __init__(self, config: Any, confirm=None) -> None:
        self.config = config
        self._max_sources = getattr(getattr(config, "agents", None), "max_research_sources", 8)

    def _llm(self, system: str, user: str, smart: bool = True) -> str:
        from ..context import get_context

        try:
            ctx = get_context()
            model = (ctx.router.cfg.smart if smart else ctx.router.cfg.fast) if ctx.router else self.config.brain.model
        except RuntimeError:
            model = self.config.brain.model

        import ollama

        client = ollama.Client(host=self.config.brain.host)
        resp = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (resp["message"].get("content") or "").strip()

    def run(self, topic: str) -> str:
        # Step 1: decompose into sub-questions
        raw = self._llm(_PLAN_SYSTEM, f"Research topic: {topic}")
        raw = re.sub(r"^```(?:json)?\s*", "", raw).strip()
        raw = re.sub(r"\s*```$", "", raw).strip()
        try:
            sub_questions: list[str] = json.loads(raw)[:5]
        except Exception:
            sub_questions = [topic]

        # Step 2: gather sources
        from ..skills.web import fetch_page, web_search

        sources: list[dict] = []
        for q in sub_questions:
            search_result = web_search(q, max_results=3)
            urls = re.findall(r"https?://[^\s\)\]]+", search_result)
            for url in urls[:2]:
                # Skip known bad URLs
                if any(bad in url for bad in ["google.com/search", "bing.com/search"]):
                    continue
                content = fetch_page(url)
                if not content.startswith("Could not") and len(content) > 100:
                    sources.append({"url": url, "question": q, "content": content[:1500]})
                if len(sources) >= self._max_sources:
                    break
            if len(sources) >= self._max_sources:
                break

        if not sources:
            return f"Could not find usable sources for '{topic}'. Try a more specific query."

        # Step 3: synthesize
        sources_text = "\n\n".join(
            f"[{i+1}] {s['url']}\n{s['content'][:800]}" for i, s in enumerate(sources)
        )
        report_md = self._llm(_SYNTH_SYSTEM, f"Topic: {topic}\n\nSources:\n{sources_text}")

        # Step 4: save report
        reports_dir = self.config.data_path / "research"
        reports_dir.mkdir(exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", topic.lower())[:50].strip("-")
        fname = f"{datetime.now():%Y%m%d-%H%M%S}-{slug}.md"
        report_path = reports_dir / fname
        report_path.write_text(f"# {topic}\n\n{report_md}", encoding="utf-8")

        # Step 5: spoken summary
        spoken = self._llm(_SPOKEN_SYSTEM, report_md, smart=False)
        return f"{spoken}\n\n(Full report: {report_path})"
