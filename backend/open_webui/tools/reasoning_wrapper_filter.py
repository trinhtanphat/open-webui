"""
title: Reasoning Auto-Wrapper Filter
description: Automatically wraps thinking/reasoning content from agents that
             don't emit <think> tags, enabling collapsible reasoning blocks in
             Open WebUI. Supports configurable end-of-thinking markers and
             smart detection of blank-line-separated reasoning paragraphs.
author: vnso
version: 1.1.0
license: MIT
"""

from pydantic import BaseModel, Field
from typing import Optional


class Filter:
    class Valves(BaseModel):
        enabled: bool = Field(
            default=True,
            description="Enable or disable this filter.",
        )
        reasoning_end_marker: str = Field(
            default="",
            description=(
                "Exact text that separates the thinking block from the answer. "
                "Examples: '---', '**Answer:**', '**Câu trả lời:**'. "
                "Leave empty to disable stream-time injection."
            ),
        )
        strip_marker_in_output: bool = Field(
            default=True,
            description=(
                "Remove the end marker from the final text "
                "(avoids showing '---' in the answer section)."
            ),
        )

    def __init__(self):
        self.valves = self.Valves()
        # Per-response streaming state (reset in outlet)
        self._think_injected: bool = False
        self._think_closed: bool = False

    # ------------------------------------------------------------------
    # STREAM — fires on every SSE chunk during generation
    # Runs BEFORE middleware's tag_output_handler, so injecting <think>
    # here causes the middleware to immediately create a reasoning block.
    # ------------------------------------------------------------------
    def stream(self, event: dict) -> dict:
        if not self.valves.enabled:
            return event

        marker = self.valves.reasoning_end_marker.strip()
        if not marker:
            return event

        choices = event.get("choices", [])
        if not choices:
            return event

        delta = choices[0].get("delta", {})
        content = delta.get("content")
        if not content:
            return event

        # ── Step 1: inject <think> on the very first content chunk ──
        if not self._think_injected:
            self._think_injected = True
            self._think_closed = False
            delta["content"] = "<think>" + content
            return event

        # ── Step 2: watch for the marker to close the thinking block ──
        if not self._think_closed and marker in content:
            self._think_closed = True
            replacement = "</think>\n\n" if self.valves.strip_marker_in_output else f"</think>\n\n{marker}"
            delta["content"] = content.replace(marker, replacement, 1)
            return event

        return event

    # ------------------------------------------------------------------
    # OUTLET — fires once after streaming completes / for non-streaming
    # Post-processes the final stored message so that previously-rendered
    # chats (or non-streaming responses) also show the collapsed block.
    # Also resets the per-response stream state.
    # ------------------------------------------------------------------
    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        # Reset stream state so the next response starts fresh
        self._think_injected = False
        self._think_closed = False

        if not self.valves.enabled:
            return body

        marker = self.valves.reasoning_end_marker.strip()
        if not marker:
            return body

        messages = body.get("messages", [])
        for msg in reversed(messages):
            if msg.get("role") != "assistant":
                continue

            content = msg.get("content", "")
            if not isinstance(content, str):
                break

            # Already has think tags — nothing to do
            if "<think>" in content:
                break

            if marker not in content:
                break

            idx = content.index(marker)
            thinking = content[:idx].rstrip()
            answer = content[idx + len(marker):].lstrip()

            if thinking:
                msg["content"] = f"<think>\n{thinking}\n</think>\n\n{answer}"
            break

        return body
