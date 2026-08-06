import json
import logging
import sys
from time import time

from starlette.middleware.base import BaseHTTPMiddleware


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        inicio = time()
        response = await call_next(request)
        duracion_ms = round((time() - inicio) * 1000, 2)
        registro = {
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duracion_ms,
        }
        logging.getLogger("app").info(json.dumps(registro))
        return response
