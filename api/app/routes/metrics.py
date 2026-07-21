from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.app.db import get_session
from api.app.schemas.metrics import MetricsResponse, SalesSummaryResponse
from api.app.services.metrics_service import MetricsService


router = APIRouter(prefix="/metrics", tags=["metrics"])


def get_metrics_service(session: Session = Depends(get_session)) -> MetricsService:
    return MetricsService(session)


def _db_error(exc: SQLAlchemyError) -> HTTPException:
    return HTTPException(status_code=500, detail=f"Database query failed: {exc}")


@router.get("/sales/summary", response_model=SalesSummaryResponse)
def sales_summary(service: MetricsService = Depends(get_metrics_service)) -> SalesSummaryResponse:
    try:
        return service.sales_summary()
    except SQLAlchemyError as exc:
        raise _db_error(exc) from exc


@router.get("/sales/monthly", response_model=MetricsResponse)
def sales_monthly(
    year: Annotated[int | None, Query(ge=2016, le=2018)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    service: MetricsService = Depends(get_metrics_service),
) -> MetricsResponse:
    try:
        return service.sales_monthly(year=year, limit=limit)
    except SQLAlchemyError as exc:
        raise _db_error(exc) from exc


@router.get("/products/performance", response_model=MetricsResponse)
def product_performance(
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    service: MetricsService = Depends(get_metrics_service),
) -> MetricsResponse:
    try:
        return service.product_performance(limit=limit)
    except SQLAlchemyError as exc:
        raise _db_error(exc) from exc


@router.get("/inventory/risk", response_model=MetricsResponse)
def inventory_risk(
    status: Annotated[str | None, Query(pattern="^(stockout|stockout_risk|overstock_risk|healthy)$")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    service: MetricsService = Depends(get_metrics_service),
) -> MetricsResponse:
    try:
        return service.inventory_risk(status=status, limit=limit)
    except SQLAlchemyError as exc:
        raise _db_error(exc) from exc


@router.get("/customers/segments", response_model=MetricsResponse)
def customer_segments(
    segment: Annotated[str | None, Query(pattern="^(vip|high_value|repeat|one_time|no_orders)$")] = None,
    state: Annotated[str | None, Query(min_length=2, max_length=2)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    service: MetricsService = Depends(get_metrics_service),
) -> MetricsResponse:
    try:
        return service.customer_segments(segment=segment, state=state, limit=limit)
    except SQLAlchemyError as exc:
        raise _db_error(exc) from exc


@router.get("/staff/performance", response_model=MetricsResponse)
def staff_performance(
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    service: MetricsService = Depends(get_metrics_service),
) -> MetricsResponse:
    try:
        return service.staff_performance(limit=limit)
    except SQLAlchemyError as exc:
        raise _db_error(exc) from exc


@router.get("/delivery/performance", response_model=MetricsResponse)
def delivery_performance(
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    service: MetricsService = Depends(get_metrics_service),
) -> MetricsResponse:
    try:
        return service.delivery_performance(limit=limit)
    except SQLAlchemyError as exc:
        raise _db_error(exc) from exc
