# Workflows en Cascada y Procesamiento por Lotes

## Problema Resuelto

### 1. Tareas en Cascada

Cuando ingieres alumnos nuevos desde SIAL, necesitas ejecutar automáticamente:

1. Crear cuenta en Teams
2. Enrolar en Moodle
3. Enviar email de bienvenida

### 2. Procesamiento Masivo

Si ingieres 200 alumnos nuevos, no puedes hacer 200 llamadas simultáneas a Microsoft Graph API porque:

- **Rate limit de Microsoft**: ~1000 requests/minuto por aplicación
- **Timeout**: El navegador/request HTTP se bloqueará
- **Sobrecarga**: Saturarás el worker de Celery

## Solución Implementada

### Arquitectura

```
Tarea de Ingesta (periódica)
    │
    │ 1. Ingesta datos desde SIAL
    │ 2. Detecta alumnos nuevos (retornar_nuevos=True)
    │ 3. Divide en lotes de 20
    ↓
┌─────────────────────────────────────┐
│ procesar_lote_alumnos_nuevos()      │
│ - Recibe: [id1, id2, ..., id20]    │
│ - Lanza workflows en paralelo       │
│ - Rate limit: 10 tareas/minuto      │
└────────┬────────────────────────────┘
         │
         │ Lanza en paralelo (con rate limiting):
         ↓
    ┌────────────────┬────────────────┬─────────────┐
    │                │                │             │
    ↓                ↓                ↓             ↓
┌────────┐      ┌────────┐      ┌────────┐    ┌────────┐
│ Alumno1│      │ Alumno2│      │ Alumno3│ ...│Alumno20│
└────┬───┘      └────┬───┘      └────┬───┘    └────┬───┘
     │               │               │             │
     │ procesar_alumno_nuevo_completo()            │
     │ (workflow completo)                         │
     ↓                                             ↓
┌─────────────────────────────────────────────────────┐
│ 1. ✓ Crear cuenta Teams (Graph API)                │
│ 2. ⏸️  Enrolar Moodle (TODO: pendiente)             │
│ 3. ✓ Enviar email bienvenida                       │
└─────────────────────────────────────────────────────┘
```

## Configuración de Batching

### Ubicación: Base de Datos (Modelo Configuracion)

La configuración de batching y rate limiting está centralizada en el modelo `Configuracion` (tabla singleton).

**Acceder desde el Admin**:

- Ir a http://localhost:8000/admin/alumnos/configuracion/
- Sección: "⚙️ Procesamiento en Lotes y Rate Limiting"

**Campos disponibles**:

- `batch_size`: Cantidad de alumnos a procesar por lote (default: 20)
- `rate_limit_teams`: Máximo de tareas Teams por minuto (default: 10)
- `rate_limit_moodle`: Máximo de tareas Moodle por minuto (default: 30)

### Ajustar según necesidad:

**batch_size (Tamaño del lote)**

- **Valor default**: 20 alumnos por lote
- **Recomendado**:
  - 10-20 para entornos con pocos workers
  - 30-50 si tienes múltiples workers de Celery
- **No exceder**: 100 (puede saturar memoria y BD)

**rate_limit_teams (Límite de velocidad para Teams)**

- **Valor default**: 10 tareas por minuto
- **Límites de Microsoft Graph API**:
  - ~1000 requests por minuto por aplicación
  - ~100 requests por segundo
- **Cálculo**:
  - Cada alumno = ~3 requests (create user + assign license + reset password)
  - 10 alumnos/min × 3 requests = 30 requests/min (seguro)
- **Ajustar**:
  - 20 = Más rápido (60 requests/min)
  - 5 = Más lento pero más seguro

**rate_limit_moodle (Límite de velocidad para Moodle)**

- **Valor default**: 30 tareas por minuto
- **Uso**: Cuando se implemente MoodleService
- **Nota**: Moodle típicamente tiene límites más permisivos que Microsoft Graph API

## Tareas Involucradas

### 1. `procesar_alumno_nuevo_completo(alumno_id, estado)`

**Descripción**: Workflow completo para un alumno nuevo.

**Parámetros**:

- `alumno_id`: ID del alumno a procesar
- `estado`: `'preinscripto'`, `'aspirante'`, o `'ingresante'`

**Workflow**:

1. **Crear cuenta en Teams**:
   
   - Llama a `TeamsService().create_user(alumno)`
   - Asigna licencia Microsoft 365 A1
   - Actualiza `alumno.email_institucional` y `alumno.teams_password`
   - Si falla: Aborta workflow (no continúa con Moodle/Email)

2. **Enrolar en Moodle** (TODO):
   
   ```python
   # Pendiente de implementar
   # moodle_svc = MoodleService()
   # moodle_result = moodle_svc.enroll_user(alumno, cursos)
   ```

3. **Enviar email de bienvenida**:
   
   - Llama a `EmailService().send_credentials_email(alumno, teams_result)`
   - Si falla: Continúa (workflow marcado como COMPLETED igual)

**Rate Limiting**:

- Implementado manualmente con `time.sleep()` en `procesar_lote_alumnos_nuevos`
- Lee el valor de `config.rate_limit_teams` de la base de datos
- Calcula delay automáticamente: `delay_seconds = 60.0 / rate_limit_teams`

**Registro en tabla Tarea**:

```json
{
  "tipo": "activar_servicios",
  "estado": "completed",
  "cantidad_entidades": 1,
  "detalles": {
    "estado": "preinscripto",
    "workflow": "completo",
    "resultados": {
      "teams": true,
      "moodle": "pending",
      "email": true,
      "errores": []
    },
    "upn": "test-a12345678@eco.unrc.edu.ar"
  }
}
```

### 2. `procesar_lote_alumnos_nuevos(alumno_ids, estado)`

**Descripción**: Orquestador que procesa lotes con rate limiting manual.

**Parámetros**:

- `alumno_ids`: Lista de IDs `[1, 2, 3, ..., 20]`
- `estado`: Estado de los alumnos

**Funcionamiento**:

1. Recibe lista de IDs

2. Lee configuración de rate limiting desde base de datos:
   
   ```python
   config = Configuracion.load()
   rate_limit = config.rate_limit_teams
   delay_seconds = 60.0 / rate_limit
   ```

3. Procesa alumnos uno por uno (síncronamente) con espera entre cada uno:
   
   ```python
   for idx, alumno_id in enumerate(alumno_ids):
       procesar_alumno_nuevo_completo(alumno_id, estado)
       if idx < len(alumno_ids) - 1:
           time.sleep(delay_seconds)  # Rate limiting
   ```

4. Cuenta éxitos y fallos

5. Actualiza registro de tarea del lote

**Resultado**:

```json
{
  "success": true,
  "total": 20,
  "exitosos": 18,
  "fallidos": 2
}
```

## Flujo Completo de Ingesta con Workflows

### Ejemplo: Ingesta de 50 Preinscriptos Nuevos

```
📅 2:00 AM - Celery Beat dispara ingesta periódica
    │
    ↓
┌─────────────────────────────────────────────────────┐
│ ingestar_preinscriptos()                            │
│ 1. Llama SIAL API                                   │
│ 2. Crea/actualiza alumnos en BD                     │
│ 3. Detecta 50 nuevos (retornar_nuevos=True)         │
└───────────────┬─────────────────────────────────────┘
                │
                │ Divide en lotes de 20
                ↓
        ┌───────┴────────┬────────────┐
        │                │            │
        ↓                ↓            ↓
    Lote 1           Lote 2       Lote 3
   (20 alumnos)    (20 alumnos) (10 alumnos)
        │                │            │
        ↓                ↓            ↓
  procesar_lote    procesar_lote procesar_lote
        │                │            │
        │ Cada lote lanza workflows en paralelo
        │ con rate limiting (10/min)
        ↓
┌──────────────────────────────────────┐
│ 20 workflows en paralelo (Lote 1)    │
│ Rate limit: Se procesan 10 por min   │
│                                      │
│ Minuto 0-1:  Alumnos 1-10            │
│ Minuto 1-2:  Alumnos 11-20           │
└──────────────────────────────────────┘

TOTAL: ~5-6 minutos para 50 alumnos
```

## Modificaciones en `ingerir_desde_sial()`

### Nueva Funcionalidad

**Parámetro**: `retornar_nuevos=True`

**Retorno anterior**:

```python
created, updated, errors = ingerir_desde_sial(tipo='preinscriptos')
```

**Retorno nuevo**:

```python
created, updated, errors, nuevos_ids = ingerir_desde_sial(
    tipo='preinscriptos',
    retornar_nuevos=True
)
# nuevos_ids = [1, 5, 12, 18, ...]  (IDs de alumnos creados)
```

### Código agregado en ingesta.py

```python
nuevos_ids: List[int] = [] if retornar_nuevos else None

for item in listas:
    # ... crear/actualizar alumno
    obj, is_created = Alumno.objects.update_or_create(...)

    # Si es nuevo y se solicitan IDs, agregarlo a la lista
    if is_created and retornar_nuevos:
        nuevos_ids.append(obj.id)

if retornar_nuevos:
    return created, updated, errors, nuevos_ids
return created, updated, errors
```

## Respuestas a tus Preguntas

### 1. ¿Dividir por número de entidades o peticiones API?

**Respuesta**: Por **número de entidades (alumnos)**.

**Razones**:

1. **Más simple**: Más fácil de entender y mantener
2. **Predecible**: Sabes exactamente cuántos alumnos estás procesando
3. **Celery rate limiting**: Ya maneja la limitación de peticiones API

**Ejemplo**:

- **Lote**: 20 alumnos
- **Peticiones por alumno**: ~3 (create user, assign license, reset password)
- **Total peticiones**: 60
- **Rate limit**: 10 alumnos/min = 30 peticiones/min (dentro del límite)

### 2. ¿Qué pasa si falla una tarea del workflow?

**Comportamiento actual**:

- **Teams falla**: Workflow se aborta (marcado como FAILED)
- **Moodle falla**: Continúa con email (cuando se implemente)
- **Email falla**: Workflow marcado como COMPLETED pero con advertencia en detalles

**Lógica**:

```python
if not teams_result:
    # Teams es crítico, abortar
    raise Exception("No se pudo crear cuenta Teams")

# Moodle y Email no son críticos
if moodle_result:
    resultados['moodle'] = True
else:
    resultados['errores'].append("Moodle: Error")
    # Continuar igual
```

### 3. ¿Cómo monitorear el progreso?

**Dashboard del Admin**:

- Ir a http://localhost:8000/admin/
- Ver "Tareas Asíncronas Recientes"
- Filtrar por tipo: "Activar Servicios"

**Tabla completa**:

- Ir a http://localhost:8000/admin/alumnos/tarea/
- Filtrar por:
  - **Estado**: `running` (en progreso), `completed`, `failed`
  - **Tipo**: `activar_servicios`
  - **Fecha**: Hoy

**Logs de Celery**:

```bash
docker logs pylucy-celery-dev --tail 100 | grep "Workflow"
```

Salida ejemplo:

```
[Workflow] Paso 1/3: Creando usuario Teams para Pérez, Juan
[Workflow] ✓ Teams creado: test-a12345678@eco.unrc.edu.ar
[Workflow] Paso 2/3: Enrolando en Moodle para Pérez, Juan
[Workflow] ⏸️  Moodle pendiente de implementar
[Workflow] Paso 3/3: Enviando email para Pérez, Juan
[Workflow] ✓ Email enviado a juan@gmail.com
[Workflow] ✓ Completado para Pérez, Juan
```

## Próximos Pasos: Implementar Moodle

### 1. Crear MoodleService

```python
# src/alumnos/services/moodle_service.py

class MoodleService:
    def enroll_user(self, alumno, estado):
        """
        Enrola alumno en cursos según su estado.

        Args:
            alumno: Instancia de Alumno
            estado: 'preinscripto', 'aspirante', 'ingresante'

        Returns:
            dict con resultado del enrolamiento
        """
        # Determinar cursos según estado
        cursos = self._get_cursos_por_estado(estado)

        # Enrolar en cada curso
        for curso in cursos:
            # Llamar API Moodle
            pass
```

### 2. Descomentar en workflow

```python
# En procesar_alumno_nuevo_completo()

# 2. Enrolar en Moodle
logger.info(f"[Workflow] Paso 2/3: Enrolando en Moodle para {alumno}")
moodle_svc = MoodleService()  # Descomentar
moodle_result = moodle_svc.enroll_user(alumno, estado)  # Descomentar
if moodle_result:
    resultados['moodle'] = True
else:
    resultados['errores'].append("Moodle: Error")
    # Continuar con email igual
```

## Configuración Recomendada por Entorno

Ajustar en el Admin: http://localhost:8000/admin/alumnos/configuracion/

### Desarrollo/Testing

- `batch_size`: 10 (lotes pequeños para debugging)
- `rate_limit_teams`: 5 (lento y seguro)
- `rate_limit_moodle`: 20

### Producción

- `batch_size`: 20 (lotes medianos)
- `rate_limit_teams`: 10 (balance entre velocidad y seguridad)
- `rate_limit_moodle`: 30

### Alta Demanda

- `batch_size`: 30 (lotes más grandes)
- `rate_limit_teams`: 15 (más rápido, requiere monitoreo)
- `rate_limit_moodle`: 50

**IMPORTANTE**: No exceder `rate_limit_teams = 20` sin monitorear rate limits de Microsoft.

## Troubleshooting

### Error: "Too Many Requests" (429) de Microsoft

**Causa**: Superaste el rate limit de Graph API

**Solución**:

1. En Admin, reducir `rate_limit_teams` a `5`
2. Reducir `batch_size` a `10`
3. Reiniciar Celery workers: `docker compose -f docker-compose.dev.yml restart celery`
4. Monitorear logs para detectar patrones

### Workflows quedan en estado RUNNING indefinidamente

**Causa**: Worker de Celery murió a mitad de ejecución

**Solución**:

```bash
# Reiniciar workers
docker compose -f docker-compose.dev.yml restart celery

# Ver tareas colgadas
# En Django shell:
from alumnos.models import Tarea
from django.utils import timezone
from datetime import timedelta

hace_1_hora = timezone.now() - timedelta(hours=1)
colgadas = Tarea.objects.filter(
    estado='running',
    hora_inicio__lt=hace_1_hora
)
print(f"Tareas colgadas: {colgadas.count()}")
```

### Lotes se procesan muy lento

**Causa**: Rate limit muy conservador

**Solución**:

1. En Admin, aumentar `rate_limit_teams` a `15` o `20`

2. Reiniciar Celery workers: `docker compose -f docker-compose.dev.yml restart celery`

3. Verificar que tienes suficientes workers:
   
   ```bash
   docker logs pylucy-celery-dev | grep "concurrency"
   ```
   
   Debería mostrar `concurrency: 4` o más

---

**Última actualización**: 2025-12-11
**Versión**: 1.0
