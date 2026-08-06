from dataclasses import dataclass

PESO_SKILLS = 70
PESO_EXPERIENCIA = 20
NORMALIZACION_EXPERIENCIA = 5
COBERTURA_SKILLS_VACIAS = 1.0

BONUS_CONTRATO = {
    "indefinido": 10,
    "obra_labor": 5,
    "prestacion_servicios": 0,
}


@dataclass(frozen=True)
class Candidato:
    skills: list[str]
    experiencia_anios: int


@dataclass(frozen=True)
class Vacante:
    skills_requeridas: list[str]
    experiencia_min: int
    tipo_contrato: str


@dataclass(frozen=True)
class ResultadoMatch:
    score: int
    categoria: str
    cobertura_skills: float
    brecha_experiencia: int
    razones: list[str]


def normalizar_skills(skills: list[str]) -> set[str]:
    """Normaliza a minúsculas y elimina duplicados antes de cualquier cálculo."""
    return {s.lower() for s in skills}


def calcular_cobertura_skills(
    skills_candidato: set[str], skills_requeridas: set[str]
) -> float:
    if not skills_requeridas:
        return COBERTURA_SKILLS_VACIAS
    coincidentes = len(skills_candidato & skills_requeridas)
    return coincidentes / len(skills_requeridas)


def calcular_brecha_experiencia(candidato: Candidato, vacante: Vacante) -> int:
    return max(0, vacante.experiencia_min - candidato.experiencia_anios)


def calcular_categoria(score: int) -> str:
    if score < 40:
        return "NO_FIT"
    if score < 65:
        return "MAYBE"
    if score < 85:
        return "GOOD_FIT"
    return "EXCELLENT_FIT"


def construir_razones(
    cobertura: float,
    coincidentes: int,
    requeridas: int,
    brecha: int,
    bonus: int,
) -> list[str]:
    razones: list[str] = []

    if requeridas > 0:
        porcentaje = round(cobertura * 100)
        razones.append(
            f"Cobertura de skills {coincidentes}/{requeridas} ({porcentaje}%)"
        )
    else:
        razones.append("Sin skills requeridas, cobertura considerada completa")

    if brecha == 0:
        razones.append("Experiencia cumple el mínimo requerido")
    else:
        razones.append(f"Brecha de experiencia: {brecha} años")

    if bonus == 10:
        razones.append("Contrato a término indefinido suma 10 puntos")
    elif bonus == 5:
        razones.append("Contrato por obra-labor suma 5 puntos")

    return razones


def calcular_match(candidato: Candidato, vacante: Vacante) -> ResultadoMatch:
    skills_candidato = normalizar_skills(candidato.skills)
    skills_requeridas = normalizar_skills(vacante.skills_requeridas)

    cobertura = calcular_cobertura_skills(skills_candidato, skills_requeridas)
    brecha = calcular_brecha_experiencia(candidato, vacante)
    bonus = BONUS_CONTRATO[vacante.tipo_contrato]

    factor_experiencia = max(0.0, 1.0 - brecha / NORMALIZACION_EXPERIENCIA)
    score = round(
        cobertura * PESO_SKILLS + factor_experiencia * PESO_EXPERIENCIA + bonus
    )

    coincidentes = len(skills_candidato & skills_requeridas)
    razones = construir_razones(
        cobertura=cobertura,
        coincidentes=coincidentes,
        requeridas=len(skills_requeridas),
        brecha=brecha,
        bonus=bonus,
    )

    return ResultadoMatch(
        score=score,
        categoria=calcular_categoria(score),
        cobertura_skills=round(cobertura, 2),
        brecha_experiencia=brecha,
        razones=razones,
    )


def calculate_match(candidato, vacante) -> dict:
    """Compatibilidad con el contrato externo test_matchv2.py.

    Recibe modelos Pydantic (o cualquier objeto con los mismos atributos)
    y devuelve un dict. La fórmula utilizada es la oficial (70/20/10).
    """
    dominio_candidato = Candidato(
        skills=candidato.skills,
        experiencia_anios=candidato.experiencia_anios,
    )
    dominio_vacante = Vacante(
        skills_requeridas=vacante.skills_requeridas,
        experiencia_min=vacante.experiencia_min,
        tipo_contrato=vacante.tipo_contrato,
    )
    resultado = calcular_match(dominio_candidato, dominio_vacante)
    return {
        "score": resultado.score,
        "categoria": resultado.categoria,
        "cobertura_skills": resultado.cobertura_skills,
        "brecha_experiencia": resultado.brecha_experiencia,
        "razones": resultado.razones,
    }
