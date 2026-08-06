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


def calcular_cobertura_skills(candidato: Candidato, vacante: Vacante) -> float:
    requeridas = vacante.skills_requeridas
    if not requeridas:
        return COBERTURA_SKILLS_VACIAS
    skills_candidato = {s.lower() for s in candidato.skills}
    skills_requeridas = {s.lower() for s in requeridas}
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
        razones.append(f"Faltan {brecha} años de experiencia")

    if bonus == 10:
        razones.append("Contrato a término indefinido suma 10 puntos")
    elif bonus == 5:
        razones.append("Contrato por obra-labor suma 5 puntos")

    return razones


def calcular_match(candidato: Candidato, vacante: Vacante) -> ResultadoMatch:
    cobertura = calcular_cobertura_skills(candidato, vacante)
    brecha = calcular_brecha_experiencia(candidato, vacante)
    bonus = BONUS_CONTRATO[vacante.tipo_contrato]

    factor_experiencia = max(0.0, 1.0 - brecha / NORMALIZACION_EXPERIENCIA)
    score = round(
        cobertura * PESO_SKILLS + factor_experiencia * PESO_EXPERIENCIA + bonus
    )

    candidatas = {s.lower() for s in candidato.skills}
    requeridas = {s.lower() for s in vacante.skills_requeridas}
    coincidentes = len(candidatas & requeridas)

    razones = construir_razones(
        cobertura=cobertura,
        coincidentes=coincidentes,
        requeridas=len(vacante.skills_requeridas),
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
