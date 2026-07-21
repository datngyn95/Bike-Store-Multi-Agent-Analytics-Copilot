from __future__ import annotations

import json
from typing import Any

from .base_agent import BaseAgent, LLMClient
from .sql_templates import SQLTemplate, templates_for_domain


class AnalyticsDomainAgent(BaseAgent):
    templates: tuple[SQLTemplate, ...]

    def __init__(
        self,
        *,
        name: str,
        domain: str,
        description: str,
        templates: tuple[SQLTemplate, ...],
        llm_client: LLMClient | None = None,
    ) -> None:
        default_tables = sorted({table for template in templates for table in template.tables})
        default_metrics = sorted({metric for template in templates for metric in template.metrics})
        super().__init__(
            name=name,
            domain=domain,
            description=description,
            llm_client=llm_client,
            default_tables=default_tables,
            default_metrics=default_metrics,
        )
        self.templates = templates

    def best_template(self, question: str) -> tuple[int, SQLTemplate | None]:
        scored = [(template.score(question), template) for template in self.templates]
        scored = [(score, template) for score, template in scored if score > 0]
        if not scored:
            return 0, None
        return sorted(scored, key=lambda item: item[0], reverse=True)[0]

    def answer_with_template(
        self,
        *,
        question: str,
        template: SQLTemplate,
        sql: str,
        rows: list[dict[str, Any]],
        warnings: list[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resolved_warnings = list(warnings or [])
        deterministic_answer = template.answer_builder(rows)
        answer = deterministic_answer

        if self.llm_client is not None:
            try:
                prompt = self._build_template_prompt(
                    question=question,
                    template=template,
                    sql=sql,
                    rows=rows,
                    deterministic_answer=deterministic_answer,
                )
                llm_answer = self.llm_client.generate(
                    prompt,
                    system_prompt=self.system_prompt,
                    temperature=0.2,
                    max_output_tokens=768,
                )
                if llm_answer:
                    answer = llm_answer
                else:
                    resolved_warnings.append("llm_empty_response")
            except Exception:
                resolved_warnings.append("llm_unavailable")

        return {
            "agent": self.name,
            "answer": answer,
            "sql": sql,
            "rows": rows,
            "metrics": list(template.metrics),
            "tables": list(template.tables),
            "filters": filters or {},
            "warnings": resolved_warnings,
            "template": template.name,
            "question": question,
        }

    def _build_template_prompt(
        self,
        *,
        question: str,
        template: SQLTemplate,
        sql: str,
        rows: list[dict[str, Any]],
        deterministic_answer: str,
    ) -> str:
        rows_preview = json.dumps(rows[:20], ensure_ascii=False, default=str, indent=2)
        extra_context = f"""
Đã xác định được SQL template an toàn và đã chạy SQL read-only.

Template: {template.name}
Mô tả template: {template.description}
Metric: {", ".join(template.metrics) or "không có"}
Bảng/mart nguồn: {", ".join(template.tables) or "không có"}

SQL đã chạy:
```sql
{sql.strip()}
```

Kết quả truy vấn: {len(rows)} dòng. Dưới đây là tối đa 20 dòng đầu:
```json
{rows_preview}
```

Tóm tắt định lượng từ SQL template:
{deterministic_answer}

Hãy kết hợp câu hỏi, SQL, metric/source và kết quả trên để trả lời bằng tiếng Việt tự nhiên.
Không chỉ lặp lại bảng số liệu; hãy nêu insight chính, nguồn dữ liệu và cảnh báo nếu kết quả rỗng.
Không suy đoán ngoài các dòng dữ liệu, metric, bảng/mart và SQL đã cung cấp.
""".strip()
        return self.build_prompt(question, {"extra_context": extra_context})

    def answer(self, question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        if context and isinstance(context.get("template"), SQLTemplate):
            return self.answer_with_template(
                question=question,
                template=context["template"],
                sql=context.get("sql", ""),
                rows=context.get("rows", []),
                warnings=context.get("warnings", []),
                filters=context.get("filters", {}),
            )
        if self.llm_client is not None:
            return super().answer(question, context)
        score, template = self.best_template(question)
        return {
            "agent": self.name,
            "answer": "Agent đã nhận câu hỏi nhưng cần query executor để chạy SQL template.",
            "sql": "",
            "rows": [],
            "metrics": list(template.metrics) if score and template else self.default_metrics,
            "tables": list(template.tables) if score and template else self.default_tables,
            "filters": {},
            "warnings": ["missing_query_executor"],
        }


class SalesAgent(AnalyticsDomainAgent):
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        super().__init__(
            name="sales_agent",
            domain="sales",
            description="Theo dõi revenue, orders, units sold, AOV, discount và sales trend.",
            templates=templates_for_domain("sales"),
            llm_client=llm_client,
        )


class CustomerAgent(AnalyticsDomainAgent):
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        super().__init__(
            name="customer_agent",
            domain="customer",
            description="Phân tích khách hàng theo state/city, top customer, frequency và revenue.",
            templates=templates_for_domain("customer"),
            llm_client=llm_client,
        )


class ProductAgent(AnalyticsDomainAgent):
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        super().__init__(
            name="product_agent",
            domain="product",
            description="Phân tích product, brand, category, model year và discount performance.",
            templates=templates_for_domain("product"),
            llm_client=llm_client,
        )


class InventoryAgent(AnalyticsDomainAgent):
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        super().__init__(
            name="inventory_agent",
            domain="inventory",
            description="Theo dõi stock quantity, sales velocity, stockout và overstock risk.",
            templates=templates_for_domain("inventory"),
            llm_client=llm_client,
        )


class StoreAgent(AnalyticsDomainAgent):
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        super().__init__(
            name="store_agent",
            domain="store",
            description="So sánh store revenue, orders, AOV, delivery delay và inventory health.",
            templates=templates_for_domain("store"),
            llm_client=llm_client,
        )


class StaffAgent(AnalyticsDomainAgent):
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        super().__init__(
            name="staff_agent",
            domain="staff",
            description="Phân tích staff revenue, order count, AOV và manager/store performance.",
            templates=templates_for_domain("staff"),
            llm_client=llm_client,
        )


class DataQualityAgent(AnalyticsDomainAgent):
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        super().__init__(
            name="data_quality_agent",
            domain="data_quality",
            description="Kiểm tra null, duplicate, foreign key, invalid dates và numeric anomalies qua read-only views.",
            templates=templates_for_domain("data_quality"),
            llm_client=llm_client,
        )


def build_default_domain_agents(llm_client: LLMClient | None = None) -> dict[str, AnalyticsDomainAgent]:
    return {
        "sales": SalesAgent(llm_client=llm_client),
        "customer": CustomerAgent(llm_client=llm_client),
        "product": ProductAgent(llm_client=llm_client),
        "inventory": InventoryAgent(llm_client=llm_client),
        "store": StoreAgent(llm_client=llm_client),
        "staff": StaffAgent(llm_client=llm_client),
        "data_quality": DataQualityAgent(llm_client=llm_client),
    }
