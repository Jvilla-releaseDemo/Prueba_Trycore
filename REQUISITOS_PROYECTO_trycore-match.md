# Requisitos del Proyecto — Microservicio de Matching Trycore

## 1. Descripción general

Microservicio HTTP que evalúa el nivel de "match" (afinidad) entre un candidato y una vacante, en función de:

- Skills declaradas
- Años de experiencia
- Tipo de contrato

El servicio debe ejecutarse **dentro de un contenedor Docker** de forma reproducible, ya que la evaluación/calificación se realizará contra el contenedor, no contra un entorno local del desarrollador.

- **Stack obligatorio:** Python + FastAPI
- **Puerto de exposición obligatorio:** `8080` (dentro y fuera del contenedor)
- **Duración máxima de desarrollo:** 1.5 horas en sesión sincrónica (hasta 100 minutos con extensiones)

---

## 2. Requisitos funcionales

### 2.1 Endpoint obligatorio

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/match` | Recibe candidato + vacante, devuelve el resultado del matching |

### 2.2 Contrato de entrada (request body)

```json
{
  "candidato": {
    "skills": ["python", "fastapi", "docker"],
    "experiencia_anios": 3
  },
  "vacante": {
    "skills_requeridas": ["python", "fastapi", "sql"],
    "experiencia_min": 2,
    "tipo_contrato": "indefinido"
  }
}
```

Campos obligatorios: `candidato.skills`, `candidato.experiencia_anios`, `vacante.skills_requeridas`, `vacante.experiencia_min`, `vacante.tipo_contrato`.

`tipo_contrato` ∈ `{"indefinido", "obra_labor", "prestacion_servicios"}`.

### 2.3 Contrato de salida (response body) — exactamente 5 campos

```json
{
  "score": 91,
  "categoria": "EXCELLENT_FIT",
  "cobertura_skills": 0.67,
  "brecha_experiencia": 0,
  "razones": [
    "Cobertura de skills 2/3 (67%)",
    "Contrato a término indefinido suma 10 puntos"
  ]
}
```

### 2.4 Lógica de negocio (implementación exacta, sin desviaciones)

```
1. cobertura_skills = len(skills ∩ skills_requeridas) / len(skills_requeridas)

2. brecha_experiencia = max(0, experiencia_min - experiencia_anios)

3. score (0–100):
   score = round(
       cobertura_skills * 70                                  # 70%
     + max(0, 1 - brecha_experiencia / 5) * 20                # 20%, normalizado a 5 años
     + bonus_contrato                                         # 10%
   )
   bonus_contrato = 10 si "indefinido", 5 si "obra_labor", 0 si "prestacion_servicios"

4. categoria:
   score < 40         -> NO_FIT
   40 <= score < 65    -> MAYBE
   65 <= score < 85    -> GOOD_FIT
   score >= 85          -> EXCELLENT_FIT

5. razones: lista de 1 a 3 strings explicando los factores de mayor peso
```

### 2.5 Validación de entrada

- Si falta cualquier campo obligatorio o el tipo es incorrecto → `HTTP 400`
- Cuerpo de error exacto:
  ```json
  { "error": "campo X requerido" }
  ```
- Implementar con validación tipada (Pydantic), no validación manual con `if`.

### 2.6 Casos borde obligatorios (deben tener test)

| Caso | Comportamiento esperado |
|---|---|
| `skills_requeridas` vacía | `cobertura_skills` determinística (decisión documentada en README, ej. `1.0`) |
| `experiencia_anios > experiencia_min` | `brecha_experiencia = 0`, no se descuenta puntaje |
| Categoría en frontera exacta (40, 65, 85) | El resultado respeta los límites `<` y `>=` tal como están definidos |

---

## 3. Requisitos no funcionales

### 3.1 Arquitectura y calidad de código

- Separación de capas obligatoria:
  - `schemas.py` → modelos Pydantic (entrada/salida)
  - `services/matching.py` → lógica pura de negocio, **sin dependencias de FastAPI/HTTP**
  - `main.py` → definición de rutas, delega el cálculo a `services/matching.py`
  - `exceptions.py` → manejo explícito de errores (nada de `except Exception` genérico)
- Código limpio, nombres descriptivos, sin lógica de negocio dentro del handler HTTP.

### 3.2 Pruebas unitarias (mínimo 5, sobre `services/matching.py`)

Casos obligatorios a cubrir:
1. `EXCELLENT_FIT` (todas las skills, experiencia ≥ mínimo, indefinido)
2. `NO_FIT` (cobertura baja o experiencia muy lejos)
3. `MAYBE`
4. `GOOD_FIT`
5. Caso borde: `skills_requeridas` vacía
6. Caso borde: `experiencia_anios` > `experiencia_min`

Comando de ejecución debe quedar documentado en el README (ej. `pytest -v`).

### 3.3 Control de versiones (Git)

- Repositorio **público** en GitHub o GitLab (sin URL privada, sin archivos comprimidos).
- Mínimo **3 commits** con mensajes descriptivos en modo imperativo:
  - ✅ `Add match endpoint`, `Add matching logic tests`, `Add Dockerfile`
  - ❌ `wip`, `cambios`, `fix`

### 3.4 Documentación — README.md (raíz del repo)

Debe incluir, como mínimo, estas secciones:

- **Cómo correr** (local y con Docker)
- **Cómo testear**
- **Decisiones tomadas** ante ambigüedades de las reglas (ej. tratamiento de `skills_requeridas` vacía)
- **Cómo construir y ejecutar el contenedor Docker** (comandos exactos)

### 3.5 Contenerización con Docker (requisito obligatorio para calificación)

> **Este es un requisito de aceptación crítico**: el evaluador probará la funcionalidad ejecutando el contenedor, no el entorno local. El servicio debe levantar sin errores solo con Docker instalado, sin pasos manuales adicionales.

#### 3.5.1 Requisitos del `Dockerfile`

- Imagen base ligera: `python:3.11-slim` (o similar).
- Copiar solo `requirements.txt` primero e instalar dependencias (aprovechar cache de capas).
- Copiar el resto del código después.
- Exponer el puerto **8080**.
- Ejecutar con un servidor de producción (`uvicorn`), no con `--reload`.
- Usuario no root recomendado (buena práctica, señal de seniority).

Ejemplo de referencia:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### 3.5.2 Comandos exactos que deben estar en el README

```bash
# Construir la imagen
docker build -t trycore-match .

# Ejecutar el contenedor
docker run -p 8080:8080 trycore-match
```

Tras ejecutar `docker run`, el servicio debe responder en `http://localhost:8080/match`.

#### 3.5.3 Criterios de aceptación específicos de Docker

| ID | Criterio | Verificación |
|---|---|---|
| D-01 | `docker build` completa sin errores | Ejecución del comando |
| D-02 | `docker run -p 8080:8080` deja el servicio escuchando | `curl http://localhost:8080/docs` responde 200 |
| D-03 | `POST /match` responde correctamente dentro del contenedor | Llamada de prueba con `curl`/Postman |
| D-04 | No se requieren pasos manuales adicionales dentro del contenedor | Solo `docker build` + `docker run` |
| D-05 | El `Dockerfile` está en la raíz del repo y documentado en el README | Revisión manual |

#### 3.5.4 `.dockerignore` recomendado

```
__pycache__/
*.pyc
.venv/
.git/
.pytest_cache/
tests/
README.md
```

### 3.6 Restricciones de tiempo y entrega

- Duración máxima: 1.5 horas (hasta 100 minutos con extensiones).
- Entrega: compartir el link al repositorio antes de cerrar la sesión. No se acepta entrega posterior.

---

## 4. Extensiones opcionales (señales de seniority, no obligatorias)

| ID | Extensión | Descripción |
|---|---|---|
| E1 | Frontend mínimo | Página HTML que consuma `/match` y muestre el resultado |
| E2 | Validación tipada | Pydantic (ya cubierto si se implementa correctamente el punto 3.1) |
| E3 | Documentación OpenAPI | Exponer `/docs` (automático con FastAPI) |
| E4 | Logging estructurado | Registrar cada request en formato JSON-lines con el score calculado |
| E5 | Dockerfile | **Pasa a ser obligatorio en este proyecto**, ya cubierto en la sección 3.5 |

---

## 5. Estructura de proyecto propuesta

```
trycore-match/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── schemas.py
│   ├── exceptions.py
│   ├── logging_config.py      # E4 (opcional)
│   └── services/
│       ├── __init__.py
│       └── matching.py
├── static/
│   └── index.html              # E1 (opcional)
├── tests/
│   └── test_matching.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
└── README.md
```

---

## 6. Checklist final de criterios de aceptación

- [ ] AC-01 Repo público (GitHub/GitLab), accesible sin auth
- [ ] AC-02 README con secciones "Cómo correr" y "Cómo testear"
- [ ] AC-03 Comando de ejecución documentado y funcional (local y Docker)
- [ ] AC-04 `POST /match` responde 200 con los 5 campos del schema
- [ ] AC-05 Los 4 casos de ejemplo (EXCELLENT_FIT, GOOD_FIT, MAYBE, NO_FIT) devuelven la categoría esperada
- [ ] AC-06 Input inválido devuelve HTTP 400 con `{ "error": "campo X requerido" }`
- [ ] AC-07 ≥ 5 pruebas unitarias sobre la lógica de matching
- [ ] AC-08 Las pruebas pasan localmente
- [ ] AC-09 ≥ 3 commits descriptivos en imperativo
- [ ] AC-10 Decisiones de ambigüedad documentadas en el README
- [ ] **D-01 a D-05** Contenedor Docker construye, expone el puerto 8080 y responde correctamente sin pasos manuales adicionales
