from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class MatchError(Exception):
    """Error base del dominio de matching."""


class MatchValidationError(MatchError):
    """Error de validación de la entrada de matching."""


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    if errors:
        loc = errors[0].get("loc", [])
        campo = ".".join(str(part) for part in loc if part != "body") or "request"
        return JSONResponse(status_code=400, content={"error": f"campo {campo} requerido"})
    return JSONResponse(status_code=400, content={"error": "campo request requerido"})


async def match_error_handler(request: Request, exc: MatchError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": str(exc)})
