import pytest

from app.schemas import MatchRequest
from app.services.matching import calculate_match


def resultado(payload: dict) -> dict:
    request_data = MatchRequest(**payload)
    return calculate_match(request_data.candidato, request_data.vacante)


def test_excellent_fit_score_maximo():
    payload = {
        "candidato": {"skills": ["python", "fastapi", "docker"], "experiencia_anios": 5},
        "vacante": {
            "skills_requeridas": ["python", "fastapi", "docker"],
            "experiencia_min": 2,
            "tipo_contrato": "indefinido",
        },
    }
    r = resultado(payload)
    assert r["score"] == 100
    assert r["categoria"] == "EXCELLENT_FIT"
    assert r["cobertura_skills"] == 1.0
    assert r["brecha_experiencia"] == 0


def test_bonus_obra_labor():
    payload = {
        "candidato": {"skills": ["python", "fastapi"], "experiencia_anios": 2},
        "vacante": {
            "skills_requeridas": ["python", "fastapi", "sql"],
            "experiencia_min": 2,
            "tipo_contrato": "obra_labor",
        },
    }
    r = resultado(payload)
    assert r["score"] == 72
    assert r["categoria"] == "GOOD_FIT"
    assert r["cobertura_skills"] == 0.67
    assert "Contrato por obra-labor suma 5 puntos" in r["razones"]


def test_no_fit_por_cobertura_y_experiencia():
    payload = {
        "candidato": {"skills": ["sql"], "experiencia_anios": 1},
        "vacante": {
            "skills_requeridas": ["python", "java", "sql", "go"],
            "experiencia_min": 8,
            "tipo_contrato": "prestacion_servicios",
        },
    }
    r = resultado(payload)
    assert r["score"] == 18
    assert r["categoria"] == "NO_FIT"
    assert "Brecha de experiencia: 7 años" in r["razones"]


def test_maybe():
    payload = {
        "candidato": {"skills": ["python"], "experiencia_anios": 1},
        "vacante": {
            "skills_requeridas": ["python", "java", "sql"],
            "experiencia_min": 1,
            "tipo_contrato": "prestacion_servicios",
        },
    }
    r = resultado(payload)
    assert r["score"] == 43
    assert r["categoria"] == "MAYBE"


def test_ejemplo_v2_score_74():
    payload = {
        "candidato": {"skills": ["java", "spring", "sql"], "experiencia_anios": 3},
        "vacante": {
            "skills_requeridas": ["java", "spring", "kafka", "sql"],
            "experiencia_min": 5,
            "tipo_contrato": "indefinido",
        },
    }
    r = resultado(payload)
    assert r["score"] == 74
    assert r["categoria"] == "GOOD_FIT"
    assert r["cobertura_skills"] == 0.75
    assert r["brecha_experiencia"] == 2
    assert r["razones"] == [
        "Cobertura de skills 3/4 (75%)",
        "Brecha de experiencia: 2 años",
        "Contrato a término indefinido suma 10 puntos",
    ]


def test_razones_maximo_tres():
    payload = {
        "candidato": {"skills": ["python", "fastapi"], "experiencia_anios": 3},
        "vacante": {
            "skills_requeridas": ["python", "fastapi", "sql"],
            "experiencia_min": 2,
            "tipo_contrato": "indefinido",
        },
    }
    r = resultado(payload)
    assert 1 <= len(r["razones"]) <= 3
