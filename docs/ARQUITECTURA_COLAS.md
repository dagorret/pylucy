# Arquitectura de Colas y Rate Limiting - PyLucy

## 📋 Visión General

PyLucy utiliza un sistema de colas basado en la base de datos (modelo `Tarea`) procesadas por Celery/Redis cada 5 minutos.

**Objetivo**: Evitar saturar las APIs externas (Teams, Moodle, UTI) respetando límites de velocidad (rate limiting) y procesando en lotes (batch processing).

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│  1. USUARIO EJECUTA ACCIÓN EN DJANGO ADMIN                      │
│  - Selecciona alumnos                                           │
│  - Clic en acción (ej: "Crear usuario en Teams")                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. ACCIÓN CREA REGISTROS EN TABLA "Tarea"                      │
│  - Un registro por cada alumno seleccionado                     │
│  - Estado inicial: PENDING                                      │
│  - NO ejecuta .delay() (no va directo a Celery)                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ↓ (espera máx 5 min)
┌─────────────────────────────────────────────────────────────────┐
│  3. CELERY BEAT EJECUTA CRON CADA 5 MINUTOS                     │
│  - Tarea: procesar_cola_tareas_pendientes()                     │
│  - Busca todas las Tareas con estado=PENDING                    │
│  - Agrupa por tipo de tarea                                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. PROCESADOR DE COLA POR LOTES                                │
│  - Por cada tipo de tarea:                                      │
│    1. Tomar hasta batch_size tareas PENDING                     │
│    2. Marcar como RUNNING                                       │
│    3. Procesar cada tarea                                       │
│    4. Aplicar rate_limit (esperar entre cada tarea)             │
│    5. Marcar como COMPLETED o FAILED                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuración (modelo `Configuracion`)

### Rate Limiting

| Parámetro | Descripción | Default | Ejemplo |
|-----------|-------------|---------|---------|
| `rate_limit_teams` | Tareas/minuto para MS Teams | 10 | 10 tareas/min = 1 cada 6 seg |
| `rate_limit_moodle` | Tareas/minuto para Moodle | 30 | 30 tareas/min = 1 cada 2 seg |
| `rate_limit_uti` | Tareas/minuto para API UTI | 20 | 20 tareas/min = 1 cada 3 seg |

### Batch Processing

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| `batch_size` | Tareas procesadas por ejecución del cron | 20 |

**Ejemplo**: Si hay 100 tareas pendientes y `batch_size=20`, el cron procesará 20 tareas cada 5 minutos.

---

## 🔄 Tipos de Tareas

Cada tipo de tarea tiene su propio rate limit y procesamiento:

| Tipo | Campo `tipo` | Rate Limit | API Usada |
|------|-------------|------------|-----------|
| Crear usuario Teams | `crear_usuario_teams` | `rate_limit_teams` | Microsoft Graph API |
| Resetear contraseña | `resetear_password` | `rate_limit_teams` | Microsoft Graph API |
| Enrollar Moodle | `moodle_enroll` | `rate_limit_moodle` | Moodle Web Services |
| Activar servicios completos | `activar_servicios` | Mix (Teams + Moodle) | Ambas APIs |
| Eliminar cuenta | `eliminar_cuenta` | Mix (Teams + Moodle) | Ambas APIs |
| Enviar email | `enviar_email` | `rate_limit_teams` | SMTP/Graph API |
| Ingesta UTI | `ingesta_*` | `rate_limit_uti` | API UTI/SIAL |

---

## 🧹 Mantenimiento Automático

### Limpieza de Resultados (celery.backend_cleanup)

**Tarea**: `celery.backend_cleanup`
**Frecuencia**: Diaria a las 4:00 AM
**Propósito**: Limpia resultados viejos almacenados en Redis

Aunque la mayoría de nuestras tareas usan `ignore_result=True`, algunos resultados se guardan en Redis. Esta tarea automática:
- Elimina resultados de tareas completadas hace más de X días (configurable)
- Previene acumulación de datos en el backend de resultados
- Mejora rendimiento general del sistema
- Se ejecuta en horario de baja actividad (4 AM)

**Configuración**: Editable desde Admin → Periodic tasks → "celery.backend_cleanup"

**¿Es necesaria?** Sí. Sin esta tarea, Redis acumularía resultados indefinidamente, consumiendo memoria y degradando el rendimiento.

---

## 📝 Modelo `Tarea`

### Estados

```python
class EstadoTarea(models.TextChoices):
    PENDING = "pending"      # En cola, esperando procesamiento
    RUNNING = "running"      # Actualmente ejecutándose
    COMPLETED = "completed"  # Finalizada exitosamente
    FAILED = "failed"        # Finalizada con error
```

### Campos clave

- `tipo`: Tipo de tarea (enum TipoTarea)
- `estado`: Estado actual (enum EstadoTarea)
- `celery_task_id`: ID de la tarea en Celery (null si aún no se procesó)
- `alumno`: FK al alumno (si aplica)
- `hora_programada`: Cuándo se creó la tarea
- `hora_inicio`: Cuándo empezó a ejecutarse
- `hora_fin`: Cuándo terminó
- `detalles`: JSON con resultados/errores
- `mensaje_error`: Texto del error si falló

---

## 🔧 Implementación Técnica

### 1. Tarea Celery del Procesador

```python
@shared_task(bind=True)
def procesar_cola_tareas_pendientes(self):
    """
    Procesa tareas pendientes respetando batch_size y rate_limits.
    Se ejecuta cada 5 minutos vía Celery Beat.
    """
    config = Configuracion.load()

    # Agrupar tareas pendientes por tipo
    tareas_por_tipo = defaultdict(list)
    tareas_pending = Tarea.objects.filter(estado=Tarea.EstadoTarea.PENDING)

    for tarea in tareas_pending[:config.batch_size]:
        tareas_por_tipo[tarea.tipo].append(tarea)

    # Procesar cada tipo con su rate limit
    for tipo, tareas in tareas_por_tipo.items():
        rate_limit = obtener_rate_limit_para_tipo(tipo, config)
        procesar_lote_por_tipo(tareas, tipo, rate_limit)
```

### 2. Rate Limiting

El rate limit se calcula así:

```python
delay_seconds = 60.0 / rate_limit  # ej: 60/10 = 6 segundos entre tareas
```

Entre cada tarea se aplica `time.sleep(delay_seconds)`.

### 3. Modificación de Acciones del Admin

**ANTES** (ejecutaba inmediatamente):
```python
@admin.action(description="👤 Crear usuario en Teams")
def crear_usuario_teams_action(self, request, queryset):
    for alumno in queryset:
        task = crear_usuario_teams_async.delay(alumno.id)  # ❌ Directo a Celery
        Tarea.objects.create(..., celery_task_id=task.id)
```

**DESPUÉS** (solo encola):
```python
@admin.action(description="👤 Crear usuario en Teams")
def crear_usuario_teams_action(self, request, queryset):
    for alumno in queryset:
        Tarea.objects.create(
            tipo=Tarea.TipoTarea.CREAR_USUARIO_TEAMS,
            estado=Tarea.EstadoTarea.PENDING,  # ✅ Solo crea registro
            alumno=alumno,
            usuario=request.user.username
        )
        # NO se llama .delay() aquí
```

### 4. Configuración de Celery Beat

```python
# src/pylucy/celery.py

app.conf.beat_schedule = {
    'procesar-cola-cada-5min': {
        'task': 'alumnos.tasks.procesar_cola_tareas_pendientes',
        'schedule': crontab(minute='*/5'),  # Cada 5 minutos
    },
    # ... otras tareas
}
```

---

## 📊 Ejemplo de Flujo Completo

### Escenario
Usuario selecciona 50 alumnos y ejecuta "Crear usuario en Teams"

**Configuración**:
- `batch_size = 20`
- `rate_limit_teams = 10` (1 tarea cada 6 segundos)

### Timeline

```
T+0 min (Usuario ejecuta acción):
├─ Se crean 50 registros Tarea con estado=PENDING
└─ Usuario ve mensaje: "50 tareas encoladas"

T+5 min (Primer cron):
├─ Procesa 20 tareas (batch_size)
├─ Marca como RUNNING
├─ Ejecuta cada una con delay de 6 seg
├─ Tiempo total: 20 × 6 seg = 2 minutos
└─ Marca 20 como COMPLETED

T+10 min (Segundo cron):
├─ Procesa siguientes 20 tareas
└─ Tiempo total: 2 minutos

T+15 min (Tercer cron):
├─ Procesa últimas 10 tareas
└─ Tiempo total: 1 minuto

TOTAL: 15 minutos para procesar 50 alumnos
```

---

## ✅ Ventajas

1. **No satura APIs**: Respeta límites de velocidad
2. **Resiliente**: Si falla una tarea, las demás continúan
3. **Auditable**: Historial completo en BD
4. **Configurable**: Ajustar rate limits sin tocar código
5. **Monitoreable**: Dashboard de Celery + tabla Tareas
6. **No bloquea UI**: Usuario recibe respuesta inmediata

---

## 🎯 Tareas Periódicas Configuradas

Todas las tareas se configuran automáticamente en la migración `0027_setup_periodic_tasks.py` y son editables desde **Admin → Periodic tasks**:

| Tarea | Frecuencia | Descripción |
|-------|------------|-------------|
| **Procesador de Cola de Tareas** | Cada 5 minutos | Procesa tareas pendientes respetando batch_size y rate_limits |
| **Ingesta Automática de Preinscriptos** | Cada 5 minutos | Ingesta desde API UTI/SIAL (verifica horario internamente) |
| **Ingesta Automática de Aspirantes** | Cada 5 minutos | Ingesta desde API UTI/SIAL (verifica horario internamente) |
| **Ingesta Automática de Ingresantes** | Cada 5 minutos | Ingesta desde API UTI/SIAL (verifica horario internamente) |
| **celery.backend_cleanup** | Diario 4:00 AM | Limpieza de resultados viejos en Redis |

**Nota**: Todas las frecuencias son configurables desde el admin sin necesidad de reiniciar servicios.

---

## 🚀 Estado de Implementación

1. ✅ Implementar `procesar_cola_tareas_pendientes()`
2. ✅ Configurar Celery Beat con DatabaseScheduler
3. ✅ Modificar acciones del admin con helper
4. ✅ Feature flag USE_QUEUE_SYSTEM
5. ✅ Migración automática de tareas periódicas
6. ✅ Documentación completa
7. ⏳ Testing con diferentes batch_size y rate_limits
8. ⏳ Dashboard de monitoreo en tiempo real

---

## 📚 Referencias

- Celery Beat: https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html
- Rate Limiting: https://en.wikipedia.org/wiki/Rate_limiting
- Microsoft Graph API limits: https://learn.microsoft.com/en-us/graph/throttling
- Moodle Web Services: https://docs.moodle.org/dev/Web_services

