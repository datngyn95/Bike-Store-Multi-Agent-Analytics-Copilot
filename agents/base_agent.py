from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Protocol

from dotenv import load_dotenv


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_FALLBACK_MODEL = "gemini-3.5-flash"


BIKE_STORE_SYSTEM_PROMPT = """
Bạn là trợ lý phân tích dữ liệu cho dự án Bike Store Multi-Agent Analytics Copilot.

Luôn tuân thủ các quy tắc bắt buộc sau:
- Luôn trả lời bằng tiếng Việt, kể cả khi người dùng hỏi bằng ngôn ngữ khác.
- Giải thích KPI ngắn gọn, rõ ràng, theo ngữ cảnh dữ liệu Bike Store.
- Chỉ diễn giải dựa trên dữ liệu, metric, bảng và kết quả truy vấn được cung cấp.
- Nếu thiếu dữ liệu hoặc metric chưa được hỗ trợ, hãy nói rõ là chưa đủ dữ liệu thay vì tự suy đoán.
- Khi có SQL hoặc nguồn dữ liệu, nêu tên metric và bảng/mart liên quan một cách minh bạch.
- Không đề xuất thao tác ghi/xóa/sửa dữ liệu; copilot analytics chỉ được dùng truy vấn đọc.
""".strip()


class LLMClient(Protocol):
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str,
        temperature: float = 0.2,
        max_output_tokens: int = 1024,
    ) -> str:
        ...


@dataclass
class GeminiClient:
    api_key: str | None = None
    model: str | None = None
    fallback_model: str | None = None

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        self.model = self.model or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
        self.fallback_model = self.fallback_model or os.getenv("GEMINI_FALLBACK_MODEL") or DEFAULT_GEMINI_FALLBACK_MODEL
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is missing. Add it to .env before using Gemini.")

        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError("google-genai is not installed. Run `pip install google-genai`.") from exc

        self._genai = genai
        self._client = genai.Client(api_key=self.api_key)

    def _generate_with_model(
        self,
        model: str,
        prompt: str,
        *,
        system_prompt: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        config = self._genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        response = self._client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
        return (response.text or "").strip()

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str,
        temperature: float = 0.2,
        max_output_tokens: int = 1024,
    ) -> str:
        try:
            return self._generate_with_model(
                self.model,
                prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
        except Exception:
            if not self.fallback_model or self.fallback_model == self.model:
                raise

            return self._generate_with_model(
                self.fallback_model,
                prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )


@dataclass
class BaseAgent:
    name: str
    domain: str
    description: str
    system_prompt: str = BIKE_STORE_SYSTEM_PROMPT
    llm_client: LLMClient | None = None
    default_tables: list[str] = field(default_factory=list)
    default_metrics: list[str] = field(default_factory=list)

    def build_prompt(self, question: str, context: dict[str, Any] | None = None) -> str:
        context = context or {}
        tables = ", ".join(self.default_tables) if self.default_tables else "chưa xác định"
        metrics = ", ".join(self.default_metrics) if self.default_metrics else "chưa xác định"
        extra_context = context.get("extra_context", "")

        return f"""
Agent: {self.name}
Lĩnh vực: {self.domain}
Mô tả nhiệm vụ: {self.description}
Metric mặc định: {metrics}
Bảng/mart mặc định: {tables}

Câu hỏi người dùng:
{question}

Ngữ cảnh bổ sung:
{extra_context}

Hãy trả lời bằng tiếng Việt theo đúng system instruction.
""".strip()

    def answer(self, question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.llm_client is None:
            raise RuntimeError(f"{self.name} has no LLM client configured.")

        prompt = self.build_prompt(question, context)
        answer = self.llm_client.generate(prompt, system_prompt=self.system_prompt)
        return {
            "agent": self.name,
            "answer": answer,
            "sql": context.get("sql") if context else None,
            "rows": context.get("rows", []) if context else [],
            "metrics": self.default_metrics,
            "tables": self.default_tables,
            "filters": context.get("filters", {}) if context else {},
            "warnings": context.get("warnings", []) if context else [],
        }
