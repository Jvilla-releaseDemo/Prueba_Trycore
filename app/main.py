import json
import logging
import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.exceptions import (
    MatchError,
    match_error_handler,
    validation_error_handler,
)
from app.logging_config import LoggingMiddleware, setup_logging
from app.schemas import MatchRequest, MatchResponse
from app.services.matching import (
    Candidato,
    Vacante,
    calcular_match,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

setup_logging()
logger = logging.getLogger("app")

app = FastAPI(title="Trycore Match", version="1.0.0")

app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(MatchError, match_error_handler)
app.add_middleware(LoggingMiddleware)


@app.post("/match", response_model=MatchResponse)
def match(payload: MatchRequest) -> MatchResponse:
    candidato = Candidato(
        skills=payload.candidato.skills,
        experiencia_anios=payload.candidato.experiencia_anios,
    )
    vacante = Vacante(
        skills_requeridas=payload.vacante.skills_requeridas,
        experiencia_min=payload.vacante.experiencia_min,
        tipo_contrato=payload.vacante.tipo_contrato,
    )
    resultado = calcular_match(candidato, vacante)
    logger.info(
        json.dumps(
            {
                "event": "match_computed",
                "score": resultado.score,
                "categoria": resultado.categoria,
            }
        )
    )
    return MatchResponse(**resultado.__dict__)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
