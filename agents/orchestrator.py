from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .base_agent import BIKE_STORE_SYSTEM_PROMPT, BaseAgent, LLMClient
from .domain_agents import AnalyticsDomainAgent, build_default_domain_agents
from .sql_guardrails import validate_readonly_sql
from .sql_templates import ALL_TEMPLATES, SQLTemplate, normalize_text


ORCHESTRATOR_SYSTEM_PROMPT = f"""
{BIKE_STORE_SYSTEM_PROMPT}

Vai trò bổ sung của Orchestrator:
- Nhận câu hỏi tiếng Việt từ người dùng.
- Xác định lĩnh vực phù hợp: sales, customer, product, inventory, store, staff hoặc data_quality.
- Chọn đúng domain agent hoặc nhiều agent nếu câu hỏi giao nhiều lĩnh vực.
- Khi tổng hợp câu trả lời, giữ câu trả lời ngắn gọn, có metric/source rõ ràng.
- Không tự bịa SQL, KPI hoặc kết quả nếu context chưa cung cấp.
""".strip()


QueryExecutor = Callable[[str], list[dict[str, Any]]]
SQLValidator = Callable[[str], str]


@dataclass
class OrchestratorAgent(BaseAgent):
    domain_agents: dict[str, AnalyticsDomainAgent] = field(default_factory=dict)

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        domain_agents: dict[str, AnalyticsDomainAgent] | None = None,
    ) -> None:
        super().__init__(
            name="orchestrator_agent",
            domain="orchestration",
            description="Phân loại intent tiếng Việt và điều phối các domain agents Bike Store.",
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            llm_client=llm_client,
            default_tables=["analytics.*", "agent.available_analytics_tables", "agent.metric_catalog"],
            default_metrics=["revenue", "orders", "units_sold", "average_order_value", "stock_quantity"],
        )
        self.domain_agents = domain_agents or {}

    @classmethod
    def with_default_agents(cls, llm_client: LLMClient | None = None) -> "OrchestratorAgent":
        return cls(llm_client=llm_client, domain_agents=build_default_domain_agents(llm_client=llm_client))

    def classify_intent(self, question: str) -> list[str]:
        normalized = normalize_text(question)
        routes: list[str] = []
        keyword_map = {
            "sales": ("doanh thu", "sales", "revenue", "don hang", "aov", "discount", "doanh so"),
            "customer": ("khach", "customer", "bang nao", "state", "city", "vip"),
            "product": ("san pham", "product", "brand", "thuong hieu", "category", "danh muc", "model"),
            "inventory": ("ton kho", "stock", "inventory", "stockout", "overstock", "ban chay", "rui ro"),
            "store": ("cua hang", "store", "giao tre", "shipment", "delivery", "ship"),
            "staff": ("nhan vien", "staff", "manager", "xu ly", "salesperson"),
            "data_quality": (
                "loi du lieu",
                "data quality",
                "null",
                "duplicate",
                "foreign key",
                "metric",
                "catalog",
                "kpi la gi",
            ),
        }

        for route, keywords in keyword_map.items():
            if any(keyword in normalized for keyword in keywords):
                routes.append(route)

        return routes or ["sales"]

    def route(self, question: str) -> list[BaseAgent]:
        route_names = self.classify_intent(question)
        agents = [self.domain_agents[name] for name in route_names if name in self.domain_agents]
        return agents or [self]

    def select_template(self, question: str) -> SQLTemplate | None:
        routed_agents = [agent for agent in self.route(question) if isinstance(agent, AnalyticsDomainAgent)]
        templates_by_name: dict[str, SQLTemplate] = {}
        for agent in routed_agents:
            for template in agent.templates:
                templates_by_name[template.name] = template

        candidates = tuple(templates_by_name.values()) or ALL_TEMPLATES
        scored = [(template.score(question), template) for template in candidates]
        scored = [(score, template) for score, template in scored if score > 0]

        if not scored and candidates is not ALL_TEMPLATES:
            scored = [(template.score(question), template) for template in ALL_TEMPLATES]
            scored = [(score, template) for score, template in scored if score > 0]

        if not scored:
            return None
        return sorted(scored, key=lambda item: (item[0], len(item[1].keywords)), reverse=True)[0][1]

    def plan(self, question: str) -> dict[str, Any]:
        template = self.select_template(question)
        return {
            "routes": self.classify_intent(question),
            "template": template.name if template else None,
            "agents": list(template.agents) if template else [self.name],
            "metrics": list(template.metrics) if template else [],
            "tables": list(template.tables) if template else [],
            "warnings": [] if template else ["unsupported_template"],
        }

    def ask(
        self,
        question: str,
        *,
        query_executor: QueryExecutor,
        row_limit: int = 100,
        sql_validator: Callable[[str, int], str] | None = None,
        ) -> dict[str, Any]:
        template = self.select_template(question)
        if template is None:
            if self.llm_client is not None:
                try:
                    prompt = self.build_prompt(
                        question,
                        {
                            "extra_context": (
                                "Khong tim thay SQL template an toan cho cau hoi nay, "
                                "vi vay khong co SQL hoac ket qua truy van du lieu. "
                                "Neu day la loi chao hoac cau hoi xa giao, hay tra loi ngan gon "
                                "va goi y nguoi dung co the hoi ve doanh thu, san pham, ton kho, "
                                "khach hang, cua hang, nhan vien hoac chat luong du lieu. "
                                "Neu day la cau hoi phan tich ngoai pham vi template, hay noi ro "
                                "copilot chua du template du lieu de tra loi bang so lieu."
                            )
                        },
                    )
                    answer = self.llm_client.generate(
                        prompt,
                        system_prompt=self.system_prompt,
                        temperature=0.2,
                        max_output_tokens=512,
                    )
                    return {
                        "agent": self.name,
                        "answer": answer or "Gemini khong tra ve noi dung cho cau hoi nay.",
                        "agents": [self.name],
                        "sql": "",
                        "rows": [],
                        "metrics": [],
                        "tables": [],
                        "filters": {},
                        "warnings": [] if answer else ["llm_empty_response"],
                    }
                except Exception:
                    return {
                        "agent": self.name,
                        "answer": (
                            "Copilot chua co SQL template cho cau hoi nay va Gemini tam thoi "
                            "chua tra loi duoc. Hay kiem tra GEMINI_API_KEY, GEMINI_MODEL "
                            "hoac log backend FastAPI."
                        ),
                        "agents": [self.name],
                        "sql": "",
                        "rows": [],
                        "metrics": [],
                        "tables": [],
                        "filters": {},
                        "warnings": ["unsupported_template", "llm_unavailable"],
                    }

            return {
                "agent": self.name,
                "answer": "Copilot chưa có SQL template cho câu hỏi này.",
                "agents": [self.name],
                "sql": "",
                "rows": [],
                "metrics": [],
                "tables": [],
                "filters": {},
                "warnings": ["unsupported_template"],
            }

        validator = sql_validator or (lambda sql, limit: validate_readonly_sql(sql, row_limit=limit))
        sql = validator(template.sql_builder(question), row_limit)
        rows = query_executor(sql)
        warnings = [] if rows else ["empty_result"]

        agent_by_name = {agent.name: agent for agent in self.domain_agents.values()}
        primary_agent = agent_by_name.get(template.agents[0])
        if primary_agent is None:
            primary_agent = AnalyticsDomainAgent(
                name=template.agents[0],
                domain=template.domain,
                description=template.description,
                templates=(template,),
                llm_client=self.llm_client,
            )

        result = primary_agent.answer_with_template(
            question=question,
            template=template,
            sql=sql,
            rows=rows,
            warnings=warnings,
        )
        result["agents"] = list(template.agents)
        return result

    def answer(self, question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        routed_agents = self.route(question)
        if routed_agents == [self] or not self.domain_agents:
            result = super().answer(question, context)
            result["agents"] = [self.name]
            return result

        child_results = [agent.answer(question, context or {}) for agent in routed_agents]
        if self.llm_client is None:
            return {
                "agent": self.name,
                "answer": "\n\n".join(result["answer"] for result in child_results),
                "agents": [result["agent"] for result in child_results],
                "sql": "",
                "rows": [],
                "metrics": sorted({metric for result in child_results for metric in result.get("metrics", [])}),
                "tables": sorted({table for result in child_results for table in result.get("tables", [])}),
                "filters": {},
                "warnings": sorted({warning for result in child_results for warning in result.get("warnings", [])}),
                "partials": child_results,
            }

        merged_context = {
            "extra_context": "\n\n".join(f"{result['agent']}: {result['answer']}" for result in child_results)
        }
        final_result = super().answer(question, merged_context)
        final_result["agents"] = [result["agent"] for result in child_results]
        final_result["partials"] = child_results
        return final_result
