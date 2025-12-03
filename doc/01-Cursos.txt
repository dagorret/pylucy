# 01-Cursos

# Diseño de mapeo de Cursos de Ingreso → Cursos de Moodle

## 1. Objetivo

Dado un lote de alumnos proveniente de una API externa (plan de estudios, carreras, materias, comisiones):

- Determinar, para cada alumno, **a qué curso de Moodle** debe inscribirse.
- La lógica depende de:
  - **Carrera** del alumno.
  - **Comisión** del alumno.
  - Si la materia/curso de ingreso tiene comportamiento **normal** o **raro** en Moodle.

---

## 2. Reglas de negocio

### 2.1 Carreras

- Las carreras vienen de otra API (plan de estudios).
- Para el módulo de ingesta se trabaja con un **diccionario pequeño y estable**:

  - Clave: `id_carrera` (numérico o código de la API).
  - Valor: `codigo_carrera` corto (ej: `"CP"`, `"LE"`, `"LA"`).

- Este diccionario se carga antes de ingresar al módulo de ingesta/procesamiento.

### 2.2 Tipos de curso de ingreso

Hay dos categorías de cursos:

1. **Cursos normales**  
   - No distinguen por comisión en Moodle.  
   - Para una carrera dada, **cualquier comisión** apunta al mismo curso de Moodle.
   - Regla:  
     - Se busca en la tabla de **CursosIngreso** por carrera (y/o materia).
     - El curso Moodle obtenido **admite todas las comisiones**.

2. **Cursos raros**  
   - Tienen comportamiento especial en Moodle; típicamente:
     - Distintos cursos de Moodle según **comisión**, o
     - Excepciones específicas para cierta carrera + comisión.
   - Regla:  
     - Se busca primero en la tabla de **CursosRaros** por:
       - Carrera
       - Comisión
     - Si hay coincidencia, el curso Moodle se toma de aquí y se ignora la definición normal.

### 2.3 Prioridad de búsqueda

Para cada alumno (carrera, comisión):

1. **Primero** se consulta si tiene un **curso raro**:
   - Buscar por (carrera, comisión) en **CursosRaros**.
   - Si existe, tomar `curso_moodle` desde ahí.

2. **Si no es raro**, se consulta la definición **normal**:
   - Buscar por carrera (y/o materia) en **CursosIngreso**.
   - El `curso_moodle` obtenido aplica para cualquier comisión.

Si nada coincide, el caso se marca como **error de mapeo** para revisión manual.

---

## 3. Modelo de datos (meta-lenguaje)

### 3.1 Diccionario de carreras (constante / JSON)

- Nombre lógico: `CARRERAS`.
- Tipo: Diccionario inmutable cargado desde un JSON o declarado como constante.
- Ejemplo conceptual:

  ```text
  CARRERAS = {
    1: "CP",
    2: "LE",
    3: "LA",
    4: "TSG",
    5: "TSI",
    6: "LAG"
  }
  ```

### 3.2 Tabla: CursosIngreso (normales)

Representa cursos de ingreso "normales", es decir, aquellos donde la comisión no altera el curso de Moodle.

Atributos:

- `id` (pk)
- `nombre` : texto corto
- `curso_moodle` : código/shortname del curso en Moodle
- `raro` : booleano (en esta etapa idealmente siempre `False`, se deja por compatibilidad)
- `carreras` : **array/lista** de códigos de carrera que usan este curso  
  - Ej: `["CP", "LE", "LA"]`

### 3.3 Tabla: CursosRaros (excepciones)

Representa excepciones por carrera + comisión.

Atributos:

- `id` (pk)
- `nombre` : texto corto (nombre descriptivo del curso de ingreso)
- `comision` : texto (ej: `"1"`, `"2"`, `"COM-01"`)
- `curso_moodle` : código/shortname del curso en Moodle
- `carreras` : array/lista de códigos de carrera a los que aplica esta excepción  
  - Ej: `["CP"]` o `["CP", "LE"]` si comparten la regla.

### 3.4 Entidades de ingesta

**No son el foco de este diseño, pero se mencionan para contexto:**

- `AlumnoAPI` (estructura que viene de la API externa):
  - `id_externo`
  - `nombre_completo`
  - `id_carrera` (numérico)
  - `comision` (texto)
  - otros campos…

- `EnrolamientoMoodle` (estructura de salida, para CSV o API):
  - `username`
  - `course_shortname`
  - `role` (student)
  - etc.

---

## 4. Flujo de procesamiento (batch)

1. **Carga de diccionario de carreras** (`CARRERAS`) desde JSON o constante.
2. **Lectura del lote de alumnos** desde la API externa.
3. Para cada alumno:
   1. Convertir `id_carrera` → `codigo_carrera` usando `CARRERAS`.
   2. Intentar resolver **curso raro** por (`codigo_carrera`, `comision`).
   3. Si no hay curso raro, resolver **curso normal** por `codigo_carrera`.
   4. Si se encuentra curso Moodle:
      - Generar registro de `EnrolamientoMoodle`.
   5. Si no se encuentra:
      - Registrar en una lista de **errores de mapeo**.
4. Generar:
   - Archivo CSV de enrolamiento para Moodle **o**
   - Payload para API de enrolamiento.
5. Opcional: reporte de casos no mapeados.

---

## 5. Interfaz de administración (Django)

- Formularios simples para:
  - Alta/edición de **CursosIngreso**.
  - Alta/edición de **CursosRaros**.
- Los campos `carreras` se administran como:
  - JSON (lista) o
  - Widget de checkboxes / multiselect que construya internamente el array.

---

## 6. Implementación en Django / Python

### 6.1 Diccionario de carreras

#### Opción A: JSON externo

```python
import json
from pathlib import Path

def load_carreras_dict():
    path = Path(__file__).resolve().parent / "carreras.json"
    return json.loads(path.read_text(encoding="utf-8"))

CARRERAS = load_carreras_dict()
```

`carreras.json`:

```json
{
  "1": "CP",
  "2": "LE",
  "3": "LA",
  "4": "TSG",
  "5": "TSI",
  "6": "LAG"
}
```

#### Opción B: Constante en código

```python
CARRERAS = {
    1: "CP",
    2: "LE",
    3: "LA",
    4: "TSG",
    5: "TSI",
    6: "LAG",
}
```

---

### 6.2 Modelos Django

```python
from django.db import models

class CursoIngreso(models.Model):
    nombre = models.CharField(max_length=30)
    curso_moodle = models.CharField(max_length=50)
    raro = models.BooleanField(default=False)
    carreras = models.JSONField(default=list)
```

---

### 6.3 Formularios Django

```python
from django import forms
from .models import CursoIngreso, CursoRaro

class CursoIngresoForm(forms.ModelForm):
    class Meta:
        model = CursoIngreso
        fields = ["nombre", "curso_moodle", "raro", "carreras"]
```

---

### 6.4 Funciones de negocio

```python
def resolver_curso_moodle(carrera_id: int, comision: str) -> Optional[str]:
    carrera_codigo = CARRERAS.get(carrera_id)
    # buscar curso raro...
    # buscar curso normal...
```

---

### 6.5 Batch de ingesta

```python
def procesar_lote_alumnos(alumnos):
    enrolamientos = []
    errores = []
    for alumno in alumnos:
        curso = resolver_curso_moodle(alumno["id_carrera"], alumno["comision"])
```

---

## 7. Posibles extensiones

- Agregar filtros por materia.
- Registrar logs de batch.
- UI para correcciones.
- 