"""HTTP API for the calculator.

Observability is built in from the start:
  * /healthz  - liveness  (is the process alive?)
  * /readyz   - readiness (should we receive traffic?)
  * /metrics  - Prometheus metrics
  * JSON logs with request ids and latency
"""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from prometheus_client import Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from . import calculator
from .config import settings
from .logging_conf import request_id_var, setup_logging

setup_logging(settings.log_level)
log = logging.getLogger("calculator.api")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(
    title="Calculator API",
    description="A tiny calculator service used to practise the deploy pipeline.",
    version=settings.version,
)

# --- custom metrics -------------------------------------------------------
CALCULATIONS = Counter(
    "calculator_operations_total",
    "Calculator operations performed, by operation and outcome.",
    ["operation", "status"],
)
APP_INFO = Gauge("calculator_app_info", "Static info about the running build.", ["version", "env"])
APP_INFO.labels(version=settings.version, env=settings.env).set(1)


# --- request logging middleware -------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    token = request_id_var.set(request_id)
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["x-request-id"] = request_id
        return response
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        # Don't let scrape traffic pollute the access log.
        if request.url.path != "/metrics":
            log.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration_ms": duration_ms,
                },
            )
        request_id_var.reset(token)


# --- schemas ---------------------------------------------------------------
class CalcRequest(BaseModel):
    operation: Literal["add", "subtract", "multiply", "divide"]
    a: float = Field(..., description="Left operand", examples=[6])
    b: float = Field(..., description="Right operand", examples=[7])


class CalcResponse(BaseModel):
    operation: str
    a: float
    b: float
    result: float


# --- routes ----------------------------------------------------------------
@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/healthz", tags=["ops"])
def healthz() -> dict[str, str]:
    """Liveness: if this fails, the container should be restarted."""
    return {"status": "ok"}


@app.get("/readyz", tags=["ops"])
def readyz() -> dict[str, str]:
    """Readiness: if this fails, traffic should be routed elsewhere.

    Add dependency checks here (database ping, cache ping) as the service grows.
    """
    return {"status": "ready", "version": settings.version, "env": settings.env}


@app.post("/api/calculate", response_model=CalcResponse, tags=["calc"])
def calculate(payload: CalcRequest) -> CalcResponse:
    try:
        result = calculator.calculate(payload.operation, payload.a, payload.b)
    except calculator.CalculatorError as err:
        CALCULATIONS.labels(payload.operation, "error").inc()
        log.warning("calculation rejected: %s", err, extra={"operation": payload.operation})
        raise HTTPException(status_code=400, detail=str(err)) from err

    CALCULATIONS.labels(payload.operation, "success").inc()
    return CalcResponse(
        operation=payload.operation,
        a=payload.a,
        b=payload.b,
        result=result,
    )


Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics", "/healthz", "/readyz"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
