"""Tiered model router.

Classifies requests and returns the appropriate Ollama model:
  fast   — simple commands, Q&A, single-step tasks   (e.g. qwen2.5:7b, stays resident)
  smart  — multi-step agentic tasks, browser, research (e.g. qwen2.5:32b, loaded on demand)
  vision — desktop screenshot + click control         (e.g. qwen2.5vl:7b, loaded on demand)
"""

from __future__ import annotations

import re

from ..config import ModelTiersConfig

_VISION_RE = re.compile(
    r"\b(screenshot|what.s on.?(the )?screen|show me (the )?screen|"
    r"desktop (task|control)|click.*(anywhere|that|on)|drag|"
    r"what.s open|taskbar|in (that |this )?app|in (word|excel|photoshop|notepad))\b",
    re.I,
)

_SMART_RE = re.compile(
    r"\b(order|buy|purchase|book|checkout|add to cart|amazon|ebay|etsy|"
    r"research|find out|look up|investigate|write.{0,10}report|summarize|"
    r"multi.?step|go to.*and|search for.*and|fill out|sign up|register|"
    r"log.?in|browse|navigate to|open.{0,20}and (then|also)|schedule|"
    r"reserve|download|install from|watch.{0,10}for|monitor|"
    r"scrape|extract from|read (the )?article|compare)\b",
    re.I,
)


class ModelRouter:
    def __init__(self, cfg: ModelTiersConfig) -> None:
        self.cfg = cfg

    def tier(self, text: str) -> str:
        """Classify text into 'fast', 'smart', or 'vision'."""
        if _VISION_RE.search(text):
            return "vision"
        if _SMART_RE.search(text):
            return "smart"
        return "fast"

    def model_for(self, text: str) -> str:
        t = self.tier(text)
        return {"fast": self.cfg.fast, "smart": self.cfg.smart, "vision": self.cfg.vision}[t]
