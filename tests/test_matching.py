from app.services.matching import (
    Candidato,
    Vacante,
    calcular_categoria,
    calcular_match,
)


def resultado(skills, exp_anios, skills_req, exp_min, contrato):
    candidato = Candidato(skills=skills, experiencia_anios=exp_anios)
    vacante = Vacante(
        skills_requeridas=skills_req,
        experiencia_min=exp_min,
        tipo_contrato=contrato,
    )
    return calcular_match(candidato, vacante)


def test_excellent_fit():
    r = resultado(
        skills=["python", "fastapi", "docker"],
        exp_anios=5,
        skills_req=["python", "fastapi", "docker"],
        exp_min=2,
        contrato="indefinido",
    )
    assert r.categoria == "EXCELLENT_FIT"
    assert r.score >= 85
    assert r.cobertura_skills == 1.0
    assert r.brecha_experiencia == 0


def test_no_fit():
    r = resultado(
        skills=["java"],
        exp_anios=1,
        skills_req=["python", "fastapi", "sql", "docker", "aws", "go"],
        exp_min=10,
        contrato="prestacion_servicios",
    )
    assert r.categoria == "NO_FIT"
    assert r.score < 40


def test_maybe():
    r = resultado(
        skills=["python"],
        exp_anios=1,
        skills_req=["python", "java", "sql"],
        exp_min=1,
        contrato="prestacion_servicios",
    )
    assert r.categoria == "MAYBE"
    assert 40 <= r.score < 65


def test_good_fit():
    r = resultado(
        skills=["python", "fastapi"],
        exp_anios=2,
        skills_req=["python", "fastapi", "sql"],
        exp_min=2,
        contrato="obra_labor",
    )
    assert r.categoria == "GOOD_FIT"
    assert 65 <= r.score < 85


def test_skills_requeridas_vacias():
    r = resultado(
        skills=["python"],
        exp_anios=0,
        skills_req=[],
        exp_min=3,
        contrato="prestacion_servicios",
    )
    assert r.cobertura_skills == 1.0


def test_experiencia_por_encima_del_minimo():
    r = resultado(
        skills=["python", "fastapi", "docker"],
        exp_anios=8,
        skills_req=["python", "fastapi", "docker"],
        exp_min=2,
        contrato="indefinido",
    )
    assert r.brecha_experiencia == 0
    assert r.score == 100


def test_categorias_en_frontera():
    assert calcular_categoria(39) == "NO_FIT"
    assert calcular_categoria(40) == "MAYBE"
    assert calcular_categoria(64) == "MAYBE"
    assert calcular_categoria(65) == "GOOD_FIT"
    assert calcular_categoria(84) == "GOOD_FIT"
    assert calcular_categoria(85) == "EXCELLENT_FIT"
