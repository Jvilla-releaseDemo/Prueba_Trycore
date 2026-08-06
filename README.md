# trycore-match

Microservicio HTTP que evalúa el nivel de **match** (afinidad) entre un candidato y una vacante en función de skills, años de experiencia y tipo de contrato. Implementado con **Python + FastAPI** y empaquetado en un contenedor Docker.

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/match` | Recibe candidato + vacante y devuelve el resultado del matching |
| `GET` | `/docs` | Documentación OpenAPI (automática de FastAPI) |
| `GET` | `/` | Frontend mínimo (E1) que consume `/match` |

## Cómo correr

### Localmente (desarrollo con uv)

Requisito: [uv](https://docs.astral.sh/uv/) instalado.

```bash
uv venv
uv pip install -r requirements.txt
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

El servicio queda en `http://localhost:8080`.

### Con Docker

```bash
# Construir la imagen
docker build -t trycore-match .

# Ejecutar el contenedor
docker run -p 8080:8080 trycore-match
```

Tras `docker run`, el servicio responde en `http://localhost:8080/match` sin pasos manuales adicionales.

## Cómo testear

```bash
uv run pytest -v
```

Cubre los 6 casos obligatorios del enunciado (EXCELLENT_FIT, NO_FIT, MAYBE, GOOD_FIT, `skills_requeridas` vacía y experiencia por encima del mínimo), las fronteras exactas de categoría (40/65/85) y la validación HTTP 400 de la API.

## Ejemplo de uso

```bash
curl -X POST http://localhost:8080/match \
  -H 'Content-Type: application/json' \
  -d '{
    "candidato": { "skills": ["python", "fastapi", "docker"], "experiencia_anios": 3 },
    "vacante": { "skills_requeridas": ["python", "fastapi", "sql"], "experiencia_min": 2, "tipo_contrato": "indefinido" }
  }'
```

Respuesta:

```json
{
  "score": 77,
  "categoria": "GOOD_FIT",
  "cobertura_skills": 0.67,
  "brecha_experiencia": 0,
  "razones": [
    "Cobertura de skills 2/3 (67%)",
    "Experiencia cumple el mínimo requerido",
    "Contrato a término indefinido suma 10 puntos"
  ]
}
```

## Cálculo del score

La fórmula de la sección 2.4 del enunciado se implementa literalmente, con estos pesos:

- **70%** — cobertura de skills: `cobertura_skills * 70`
- **20%** — experiencia, normalizada a 5 años: `max(0, 1 - brecha_experiencia / 5) * 20`
- **10%** — bonus por tipo de contrato: `10` indefinido, `5` obra_labor, `0` prestacion_servicios

```
score = round(cobertura_skills * 70 + max(0, 1 - brecha_experiencia / 5) * 20 + bonus_contrato)
```

Ejemplo verificado (candidato `java/spring/sql` con 3 años vs vacante que pide `java/spring/kafka/sql` con mínimo 5 años, contrato indefinido → **score 74**):

```
cobertura_skills = 3/4 = 0.75          → 0.75 × 70 = 52.5
brecha_experiencia = max(0, 5-3) = 2    → max(0, 1 - 2/5) × 20 = 12
bonus_contrato (indefinido)             → 10
score = round(52.5 + 12 + 10) = 74      → GOOD_FIT
```

## Decisiones que tomaste

| Ambigüedad | Decisión |
|---|---|
| `skills_requeridas` vacía | `cobertura_skills = 1.0` (no hay skills que cubrir; se otorga el 100% del peso de skills) |
| **Discrepancia del ejemplo del enunciado (score 91 vs 77)** | El documento fuente muestra `score: 91` con cobertura 2/3 + contrato indefinido, pero aplicando la fórmula formal del punto 2.4 (`cobertura*70 + exp*20 + bonus*10`) el resultado es `round(46.67 + 20 + 10) = 77`. Se implementó **la fórmula literal** (sección 2.4, que es la especificación que manda) y esta discrepancia queda documentada como decisión consciente, no como bug. |
| Comparación de skills | Case-insensitive: `"Python"` y `"python"` se consideran la misma skill (se normalizan a minúsculas antes de intersectar) |
| `brecha_experiencia` | Solo se descuenta cuando `experiencia_anios < experiencia_min`; si el candidato supera el mínimo, `brecha = 0` y no hay penalización |
| Redondeo del score | Se usa `round()` de Python sobre el total con fórmula; se devuelve `cobertura_skills` redondeada a 2 decimales |
| Error de validación | La validación es tipada con Pydantic; los errores `422` de FastAPI se convierten en `HTTP 400` con el formato `{"error": "campo X requerido"}` (con el path del campo, ej. `campo vacante.tipo_contrato requerido`) |

## Arquitectura

```
trycore-match/
├── app/
│   ├── main.py              # Definición de rutas; delega el cálculo al servicio
│   ├── schemas.py           # Modelos Pydantic (entrada/salida)
│   ├── exceptions.py        # Manejo explícito de errores y handlers HTTP 400
│   ├── logging_config.py    # E4: logging estructurado JSON-lines por request
│   └── services/
│       └── matching.py      # Lógica pura de negocio, sin dependencias de FastAPI/HTTP
├── static/
│   └── index.html           # E1: frontend mínimo
├── tests/
│   ├── test_matching.py     # Pruebas de la lógica de matching
│   ├── test_matchv3.py      # Escenarios de score calculados (incluye score 74)
│   └── test_api.py          # Pruebas del endpoint HTTP
├── requirements.txt
├── Dockerfile
├── .dockerignore
└── .gitignore
```

## Extensiones opcionales implementadas

- **E1 — Frontend mínimo**: `static/index.html`, servido en `/`.
- **E2 — Validación tipada**: modelos Pydantic en `app/schemas.py`.
- **E3 — Documentación OpenAPI**: `/docs` habilitado por FastAPI.
- **E4 — Logging estructurado**: cada request se registra en JSON-lines a stdout; para `/match` se incluye además el score y la categoría calculados.
