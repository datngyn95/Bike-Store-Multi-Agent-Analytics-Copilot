from __future__ import annotations

from types import SimpleNamespace

from agents.base_agent import DEFAULT_GEMINI_FALLBACK_MODEL, DEFAULT_GEMINI_MODEL, GeminiClient


class FakeModels:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def generate_content(self, *, model: str, contents: str, config: object) -> SimpleNamespace:
        self.calls.append(model)
        if model == DEFAULT_GEMINI_MODEL:
            raise RuntimeError("429 RESOURCE_EXHAUSTED")
        return SimpleNamespace(text=" fallback answer ")


def test_gemini_client_defaults_to_25_flash_with_35_flash_fallback():
    assert DEFAULT_GEMINI_MODEL == "gemini-2.5-flash"
    assert DEFAULT_GEMINI_FALLBACK_MODEL == "gemini-3.5-flash"


def test_gemini_client_uses_fallback_model_when_primary_fails():
    fake_models = FakeModels()
    client = GeminiClient.__new__(GeminiClient)
    client.model = DEFAULT_GEMINI_MODEL
    client.fallback_model = DEFAULT_GEMINI_FALLBACK_MODEL
    client._genai = SimpleNamespace(types=SimpleNamespace(GenerateContentConfig=lambda **kwargs: kwargs))
    client._client = SimpleNamespace(models=fake_models)

    answer = client.generate("prompt", system_prompt="system")

    assert answer == "fallback answer"
    assert fake_models.calls == [DEFAULT_GEMINI_MODEL, DEFAULT_GEMINI_FALLBACK_MODEL]
