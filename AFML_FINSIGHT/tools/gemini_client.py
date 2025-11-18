"""Gemini API client wrapper for FinSight tools and agents."""
from __future__ import annotations

from typing import Any, Dict, Sequence

import google.generativeai as genai

from AFML_FINSIGHT.config.settings import get_settings


class GeminiClient:
    """Lightweight Gemini client helper."""

    def __init__(self, model_name: str = "models/gemini-flash-latest") -> None:
        settings = get_settings()
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(model_name=model_name)
        self.model_name = model_name

    @staticmethod
    def _response_text(response: Any) -> str:
        if not response:
            return ""
        text = getattr(response, "text", None)
        if text:
            return text

        candidates = getattr(response, "candidates", None) or []
        collected: list[str] = []
        for candidate in candidates:
            candidate_text = getattr(candidate, "text", None)
            if candidate_text:
                collected.append(candidate_text)
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) if content else None
            if parts:
                for part in parts:
                    part_text = getattr(part, "text", None)
                    if part_text:
                        collected.append(part_text)
        return "\n".join(collected)

    @staticmethod
    def _finish_reason(response: Any) -> str:
        candidates = getattr(response, "candidates", None) or []
        if not candidates:
            return "unknown"
        reason = getattr(candidates[0], "finish_reason", None)
        return str(reason) if reason is not None else "unknown"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        response = self.model.generate_content(prompt, **kwargs)
        text = self._response_text(response)
        if not text:
            reason = self._finish_reason(response)
            raise RuntimeError(f"Gemini returned no text (finish_reason={reason})")
        return text

    def generate_structured(self, prompt: str, mime_type: str = "application/json", **kwargs: Any) -> Dict[str, Any]:
        response = self.model.generate_content(prompt, generation_config={"response_mime_type": mime_type}, **kwargs)
        text = self._response_text(response) or "{}"
        import json

        return json.loads(text)

    def function_call(self, prompt: str, tools: Sequence[Dict[str, Any]]) -> Any:
        model = genai.GenerativeModel(model_name=self.model_name, tools=tools)
        response = model.generate_content(prompt)
        return response

    def generate_multimodal(self, parts: Sequence[Any], **kwargs: Any) -> str:
        model = genai.GenerativeModel(model_name=self.model_name)
        response = model.generate_content(parts, **kwargs)
        text = self._response_text(response)
        if text:
            return text
        reason = self._finish_reason(response)
        return f"REVISE: Gemini returned no feedback (finish_reason={reason})."
