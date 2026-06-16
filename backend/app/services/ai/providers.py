"""
Concrete providers.

- NullProvider   : always returns None -> forces the deterministic fallback.
                   Used when AI_PROVIDER="none" or no API key is configured.
- OpenAIProvider : OpenAI Chat Completions, JSON response mode.
- GeminiProvider : Google Gemini generateContent, JSON response mode
                   (free tier, no prepaid credits needed).

Both real providers swallow every error and return None, so a bad key,
network blip, rate limit, or malformed response can never crash a request.
"""
import json

import httpx

_TIMEOUT = httpx.Timeout(20.0)


class NullProvider:
    name = "null"

    def complete_json(self, system: str, user: str) -> dict | None:
        return None


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._api_key = api_key
        self._model = model

    def complete_json(self, system: str, user: str) -> dict | None:
        try:
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.4,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception:
            return None


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        self._api_key = api_key
        self._model = model

    def complete_json(self, system: str, user: str) -> dict | None:
        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self._model}:generateContent?key={self._api_key}"
            )
            resp = httpx.post(
                url,
                json={
                    "system_instruction": {"parts": [{"text": system}]},
                    "contents": [{"parts": [{"text": user}]}],
                    "generationConfig": {"response_mime_type": "application/json"},
                },
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except Exception:
            return None
