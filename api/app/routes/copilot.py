from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.app.db import get_session
from api.app.schemas.copilot import CopilotRequest, CopilotResponse
from api.app.services.copilot_service import CopilotService
from api.app.services.sql_guardrails import SQLGuardrailError


router = APIRouter(prefix="/copilot", tags=["copilot"])


def get_copilot_service(session: Session = Depends(get_session)) -> CopilotService:
    return CopilotService(session)


@router.post("/ask", response_model=CopilotResponse)
def ask_copilot(
    request: CopilotRequest,
    service: CopilotService = Depends(get_copilot_service),
) -> CopilotResponse:
    try:
        return service.ask(request.question, limit=request.limit)
    except SQLGuardrailError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=f"Database query failed: {exc}") from exc
