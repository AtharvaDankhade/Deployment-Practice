"""Structured JSON logging.

Logs go to stdout as one JSON object per line, which is what log collectors
(Docker, Loki, CloudWatch, Datadog...) expect. Every line carries the request id
so a single request can be followed end to end.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar

# Set by the request middleware; read by the formatter.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

_EXTRA_FIELDS = ("method", "path", "status", "duration_ms", "operation")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # We emit our own JSON access log, so silence uvicorn's plain-text one.
    logging.getLogger("uvicorn.access").disabled = True
