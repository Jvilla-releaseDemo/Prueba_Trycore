from typing import List, Literal

from pydantic import BaseModel

TipoContrato = Literal["indefinido", "obra_labor", "prestacion_servicios"]


class Candidato(BaseModel):
    skills: List[str]
    experiencia_anios: int


class Vacante(BaseModel):
    skills_requeridas: List[str]
    experiencia_min: int
    tipo_contrato: TipoContrato


class MatchRequest(BaseModel):
    candidato: Candidato
    vacante: Vacante


class MatchResponse(BaseModel):
    score: int
    categoria: str
    cobertura_skills: float
    brecha_experiencia: int
    razones: List[str]
