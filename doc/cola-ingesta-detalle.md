# Diferencia entre Frecuencia de Ingesta y Rate Limiting de Procesamiento

## Resumen

Hay **dos conceptos diferentes** que trabajan juntos pero tienen propósitos distintos:

1. **Frecuencia de Ingesta** (`preinscriptos_frecuencia_segundos`): Cada cuánto tiempo consultar SIAL
2. **Rate Limiting de Procesamiento** (`batch_size`, `rate_limit_teams`): Cómo procesar los alumnos encontrados

---

## 1. Frecuencia de Ejecución (Celery Beat)

**`preinscriptos_frecuencia_segundos`** controla **cada cuánto tiempo se ejecuta la tarea de ingesta automática**

- Ejemplo: `3600 segundos = 1 hora`
- Significa: Cada 1 hora, Celery Beat dispara la tarea `ingestar_preinscriptos()`
- **Esto consulta SIAL** y trae alumnos nuevos

**Código donde se usa:**
- `src/alumnos/management/commands/setup_periodic_tasks.py` (configura Celery Beat)

```python
# Cada X segundos, ejecutar la tarea
schedule=crontab(minute=f'*/{config.preinscriptos_frecuencia_segundos // 60}')
```

---

## 2. Rate Limiting (Procesamiento)

**`rate_limit_teams`** y **`batch_size`** controlan **cómo procesar los alumnos una vez que llegan**

- Ejemplo: `rate_limit_teams = 10` → Procesa 10 alumnos por minuto
- **Esto NO afecta cada cuánto se ejecuta la ingesta**, sino **cómo se procesan los workflows**

---

## Relación entre ambos

**SÍ están relacionados, pero son independientes:**

```
[Cada 1 hora] → Celery Beat dispara ingesta
                    ↓
            ingestar_preinscriptos()
                    ↓
            Consulta SIAL, encuentra 50 nuevos
                    ↓
            [batch_size=20] Divide en 3 lotes
                    ↓
            Lote 1 (20 alumnos) → [rate_limit_teams=10] Procesa a 10/min
            Lote 2 (20 alumnos) → [rate_limit_teams=10] Procesa a 10/min
            Lote 3 (10 alumnos) → [rate_limit_teams=10] Procesa a 10/min
                    ↓
            Termina en ~5 minutos
                    ↓
            [Espera 55 minutos hasta la próxima ejecución]
```

---

## Parámetros Explicados

### BATCH_SIZE (batch_size)

**¿Qué es?** Cuántos alumnos procesar en cada "tanda" o "grupo"

**Ejemplo práctico:**
- Llegan 100 alumnos nuevos desde SIAL
- Con `batch_size = 20`:
  - Se crean 5 tandas de 20 alumnos cada una
  - Tanda 1: alumnos 1-20
  - Tanda 2: alumnos 21-40
  - Tanda 3: alumnos 41-60
  - etc.

**¿Por qué dividir?**
- Si procesas 100 alumnos de golpe, saturas el sistema
- Es mejor dividir en grupos más pequeños y manejables

### RATE_LIMIT (rate_limit_teams / rate_limit_moodle)

**¿Qué es?** Cuántos alumnos procesar **por minuto** dentro de cada tanda

**Ejemplo práctico con rate_limit_teams = 10:**
- Tienes una tanda de 20 alumnos
- El sistema procesa **máximo 10 alumnos por minuto**
- Entonces esa tanda de 20 tarda **2 minutos** en completarse
- Entre alumno y alumno espera: 60 segundos ÷ 10 = **6 segundos**

**¿Por qué limitar la velocidad?**
- Microsoft Graph API tiene límites: si envías demasiadas peticiones muy rápido, te bloquea con error 429 ("Too Many Requests")
- El rate limit evita saturar la API de Microsoft o Moodle

### FRECUENCIA (preinscriptos_frecuencia_segundos)

**¿Qué es?** Cada cuántos segundos se ejecuta la tarea de ingesta automática

**Ejemplo práctico con frecuencia = 3600:**
- Cada 3600 segundos (1 hora) Celery Beat dispara `ingestar_preinscriptos()`
- La tarea consulta SIAL y trae los alumnos nuevos
- Luego los procesa según `batch_size` y `rate_limit_teams`

**¿Por qué configurar esto?**
- Durante período de inscripción: Frecuencia alta (ej: 1 hora = 3600 segundos)
- Fuera de período de inscripción: Frecuencia baja o desactivar

---

## Ejemplo Completo

**Escenario**: Llegan 50 preinscriptos nuevos

**Configuración:**
- `preinscriptos_frecuencia_segundos = 3600` (1 hora)
- `batch_size = 20`
- `rate_limit_teams = 10`

**¿Qué pasa?**

1. **División en lotes:**
   - Lote 1: 20 alumnos (IDs 1-20)
   - Lote 2: 20 alumnos (IDs 21-40)
   - Lote 3: 10 alumnos (IDs 41-50)

2. **Procesamiento del Lote 1 (20 alumnos):**
   - Rate limit = 10/min → Procesa 10 alumnos por minuto
   - Minuto 0-1: Procesa alumnos 1-10
   - Minuto 1-2: Procesa alumnos 11-20
   - **Tiempo total lote 1: 2 minutos**

3. **Procesamiento del Lote 2 (20 alumnos):**
   - Igual que lote 1
   - **Tiempo total lote 2: 2 minutos**

4. **Procesamiento del Lote 3 (10 alumnos):**
   - Solo 10 alumnos
   - **Tiempo total lote 3: 1 minuto**

**Tiempo total para los 50 alumnos: ~5 minutos**

---

## Diferencia entre Teams y Moodle

**rate_limit_teams = 10** (más lento)
- Microsoft Graph API es muy estricto
- Si envías demasiadas peticiones, te bloquea

**rate_limit_moodle = 30** (más rápido)
- Moodle tolera más carga
- Puedes procesar 30 alumnos por minuto sin problema

---

## Timeline Real

**Configuración:**
- `preinscriptos_frecuencia_segundos = 3600` (1 hora)
- `batch_size = 20`
- `rate_limit_teams = 10`

**Timeline:**
```
10:00 AM → Celery Beat ejecuta ingesta
           Encuentra 50 preinscriptos nuevos
           Los procesa en 5 minutos (3 lotes de 20)
10:05 AM → Termina procesamiento
           [ESPERA 55 MINUTOS]

11:00 AM → Celery Beat ejecuta ingesta nuevamente
           Encuentra 10 preinscriptos nuevos
           Los procesa en 1 minuto (1 lote de 10)
11:01 AM → Termina procesamiento
           [ESPERA 59 MINUTOS]

12:00 PM → Celery Beat ejecuta ingesta nuevamente
           No encuentra nuevos
           No hay nada que procesar
           [ESPERA 1 HORA]

13:00 PM → Celery Beat ejecuta ingesta nuevamente
           ...
```

---

## ¿Cómo ajustar según tu caso?

### Si quieres INGESTAR más seguido:
- ↓ Reduce `preinscriptos_frecuencia_segundos` (ej: 1800 = cada 30 minutos)
- Útil durante períodos de alta inscripción

### Si quieres PROCESAR más rápido:
- ↑ Aumenta `batch_size` (ej: 30 o 50)
- ↑ Aumenta `rate_limit_teams` (ej: 15 o 20)
- ⚠️ Riesgo: Puedes saturar la API de Microsoft

### Si tienes errores 429 ("Too Many Requests"):
- ↓ Reduce `rate_limit_teams` (ej: 5)
- ↓ Reduce `batch_size` (ej: 10)
- ✅ Más seguro pero más lento

### Si quieres pausar la ingesta:
- Deja `preinscriptos_dia_inicio` vacío (NULL)
- O configura `preinscriptos_dia_fin` en el pasado

---

## Propuesta de Mejora en el Admin

### Fieldsets Actuales

```python
('⚙️ Procesamiento en Lotes y Rate Limiting', {
    'fields': (
        'batch_size',
        'rate_limit_teams',
        'rate_limit_moodle',
    ),
    'description': 'Configuración de workflows automáticos...'
}),

('📅 Ingesta de Preinscriptos', {
    'fields': (
        'preinscriptos_dia_inicio',
        'preinscriptos_dia_fin',
        'preinscriptos_frecuencia_segundos',
    ),
}),
```

### Propuesta de Mejora

**Separar claramente los conceptos:**

```python
('📅 Programación de Ingestas Automáticas', {
    'fields': (
        'preinscriptos_dia_inicio',
        'preinscriptos_dia_fin',
        'preinscriptos_frecuencia_segundos',
    ),
    'description': '''
    Controla CUÁNDO y cada CUÁNTO TIEMPO se ejecuta la ingesta automática desde SIAL.
    - dia_inicio/dia_fin: Ventana de tiempo en que está activa la ingesta
    - frecuencia_segundos: Cada cuántos segundos se consulta SIAL (ej: 3600 = cada 1 hora)
    '''
}),

('⚙️ Procesamiento de Workflows (Teams + Moodle + Email)', {
    'fields': (
        'batch_size',
        'rate_limit_teams',
        'rate_limit_moodle',
    ),
    'description': '''
    Controla CÓMO se procesan los alumnos encontrados en cada ingesta.
    - batch_size: Cantidad de alumnos por tanda (ej: 20 = divide 100 alumnos en 5 tandas)
    - rate_limit_teams: Máximo de alumnos a procesar por minuto en Teams (ej: 10 = procesa 10/min)
    - rate_limit_moodle: Máximo de alumnos a procesar por minuto en Moodle (ej: 30 = procesa 30/min)
    '''
}),
```

---

## Resumen de Responsabilidades

| Parámetro | ¿Qué controla? | Ejemplo |
|-----------|----------------|---------|
| `preinscriptos_dia_inicio` | Cuándo **EMPEZAR** a ingestar | 2025-03-01 00:00 |
| `preinscriptos_dia_fin` | Cuándo **TERMINAR** de ingestar | 2025-04-30 23:59 |
| `preinscriptos_frecuencia_segundos` | Cada **CUÁNTO TIEMPO** ingestar | 3600 = cada 1 hora |
| `batch_size` | Cuántos alumnos por **TANDA** | 20 = tandas de 20 |
| `rate_limit_teams` | Cuántos alumnos por **MINUTO** (Teams) | 10 = 10 alumnos/min |
| `rate_limit_moodle` | Cuántos alumnos por **MINUTO** (Moodle) | 30 = 30 alumnos/min |

---

**Última actualización**: 2025-12-11
**Versión**: 1.0
