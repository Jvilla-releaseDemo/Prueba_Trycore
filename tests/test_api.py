from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_match_endpoint_ok():
    payload = {
        "candidato": {
            "skills": ["python", "fastapi", "docker"],
            "experiencia_anios": 3,
        },
        "vacante": {
            "skills_requeridas": ["python", "fastapi", "sql"],
            "experiencia_min": 2,
            "tipo_contrato": "indefinido",
        },
    }
    res = client.post("/match", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert set(body.keys()) == {
        "score",
        "categoria",
        "cobertura_skills",
        "brecha_experiencia",
        "razones",
    }


def test_match_campo_faltante_devuelve_400():
    payload = {
        "candidato": {
            "skills": ["python"],
            "experiencia_anios": 3,
        },
        "vacante": {
            "skills_requeridas": ["python"],
            "experiencia_min": 2,
        },
    }
    res = client.post("/match", json=payload)
    assert res.status_code == 400
    assert "error" in res.json()
    assert "tipo_contrato" in res.json()["error"]


def test_match_tipo_incorrecto_devuelve_400():
    payload = {
        "candidato": {
            "skills": ["python"],
            "experiencia_anios": "tres",
        },
        "vacante": {
            "skills_requeridas": ["python"],
            "experiencia_min": 2,
            "tipo_contrato": "indefinido",
        },
    }
    res = client.post("/match", json=payload)
    assert res.status_code == 400
    assert "error" in res.json()
