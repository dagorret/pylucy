# 🧪 Guía de Pruebas: Sistema de Colas PyLucy

## 📋 Estado Actual del Sistema

### ✅ Configuración Completada

1. **Tareas Periódicas** (django-celery-beat)
   - ✅ 5 tareas configuradas en BD (editables desde Admin)
   - ✅ Celery Beat usa `DatabaseScheduler` (no hardcoded)
   - ✅ Todas ejecutan cada 5 minutos (`*/5 * * * *`)

2. **Sistema de Colas**
   - ✅ Feature flag `USE_QUEUE_SYSTEM` implementado
   - ✅ Helper `encolar_o_ejecutar_tarea()` aplicado a 7 acciones
   - ✅ Procesador de cola con batch_size y rate_limits

3. **Admin Simplificado**
   - ✅ Solo muestra: Periodic tasks, Crontab schedules
   - ❌ Eliminado: Interval, Clocked, Solar schedules

---

## 🎯 Modos de Operación

### Modo A: LEGACY (por defecto)
```bash
# En .env (o sin definir la variable)
USE_QUEUE_SYSTEM=false
```
**Comportamiento:**
- Las acciones ejecutan `.delay()` inmediatamente
- Tareas se procesan al instante vía Celery workers
- **NO respeta** batch_size ni rate_limits

### Modo B: QUEUE (nuevo sistema)
```bash
# En .env
USE_QUEUE_SYSTEM=true
```
**Comportamiento:**
- Las acciones crean registros `Tarea(estado=PENDING)`
- El cron procesa tareas cada 5 minutos
- **SÍ respeta** batch_size y rate_limits

---

## 🧪 Plan de Pruebas

### Prueba 1: Verificar Configuración Actual

```bash
# Ver tareas periódicas configuradas
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
for task in PeriodicTask.objects.filter(enabled=True):
    print(f'✅ {task.name} → {task.crontab}')
"

# Ver modo actual (queue o legacy)
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django.conf import settings
mode = 'QUEUE' if getattr(settings, 'USE_QUEUE_SYSTEM', False) else 'LEGACY'
print(f'Modo actual: {mode}')
"

# Ver configuración de batch_size y rate_limits
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Configuracion
config = Configuracion.load()
print(f'batch_size: {config.batch_size}')
print(f'rate_limit_teams: {config.rate_limit_teams}')
print(f'rate_limit_moodle: {config.rate_limit_moodle}')
print(f'rate_limit_uti: {config.rate_limit_uti}')
"
```

---

### Prueba 2: Modo LEGACY (ejecución inmediata)

```bash
# 1. Asegurar que USE_QUEUE_SYSTEM=false
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django.conf import settings
print('USE_QUEUE_SYSTEM:', getattr(settings, 'USE_QUEUE_SYSTEM', False))
"

# 2. Desde Django Admin:
#    - Ir a: http://localhost:8001/admin/
#    - Alumnos → Seleccionar 2-3 alumnos
#    - Acción: "👤 Crear usuario en Teams (sin email)"
#    - Mensaje esperado: "X tareas PROGRAMADAS"

# 3. Verificar que se ejecutaron INMEDIATAMENTE
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Tarea
tareas = Tarea.objects.filter(tipo='crear_usuario_teams').order_by('-hora_programada')[:5]
for t in tareas:
    print(f'{t.alumno}: {t.estado} (celery_id: {t.celery_task_id})')
"
# Debe mostrar: celery_task_id != None (se llamó .delay())
```

---

### Prueba 3: Modo QUEUE (sistema de colas)

```bash
# 1. ACTIVAR el sistema de colas
# Editar .env.testing.real (o el que uses) y agregar:
echo "USE_QUEUE_SYSTEM=true" >> .env.testing.real

# 2. Reiniciar servicios
docker compose -f docker-compose.testing.yml restart web celery celery-beat

# 3. Verificar que se activó
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django.conf import settings
print('USE_QUEUE_SYSTEM:', settings.USE_QUEUE_SYSTEM)
"
# Debe mostrar: True

# 4. Crear tareas desde Admin
#    - Seleccionar 5 alumnos
#    - Acción: "👤 Crear usuario en Teams (sin email)"
#    - Mensaje esperado: "5 tareas ENCOLADAS"

# 5. Verificar que están PENDING (sin celery_task_id)
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Tarea
tareas = Tarea.objects.filter(tipo='crear_usuario_teams', estado='pending')
print(f'Tareas PENDING: {tareas.count()}')
for t in tareas:
    print(f'  - {t.alumno}: celery_id={t.celery_task_id}')
"
# Debe mostrar: celery_task_id=None

# 6. Opción A: Esperar 5 minutos (el cron las procesará)
# Opción B: Forzar ejecución del procesador
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.tasks import procesar_cola_tareas_pendientes
procesar_cola_tareas_pendientes()
"

# 7. Verificar que se procesaron
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Tarea
completadas = Tarea.objects.filter(tipo='crear_usuario_teams', estado='completed').count()
fallidas = Tarea.objects.filter(tipo='crear_usuario_teams', estado='failed').count()
print(f'Completadas: {completadas}')
print(f'Fallidas: {fallidas}')
"
```

---

### Prueba 4: Rate Limiting

```bash
# 1. Configurar rate_limit bajo para ver el efecto
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Configuracion
config = Configuracion.load()
config.rate_limit_teams = 5  # 5 tareas/min = 1 tarea cada 12 seg
config.save()
print('rate_limit_teams configurado a 5 tareas/min')
"

# 2. Crear 10 tareas de Teams
#    - Desde Admin, seleccionar 10 alumnos
#    - Acción: "👤 Crear usuario en Teams"

# 3. Forzar procesamiento y medir tiempo
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
import time
from alumnos.tasks import procesar_cola_tareas_pendientes
inicio = time.time()
procesar_cola_tareas_pendientes()
fin = time.time()
print(f'Tiempo total: {fin - inicio:.2f} segundos')
print(f'Esperado: ~120 segundos (10 tareas × 12 seg/tarea)')
"

# 4. Ver logs detallados
docker compose -f docker-compose.testing.yml logs celery | grep -E "(Cola|rate_limit|delay)"
```

---

### Prueba 5: Batch Size

```bash
# 1. Configurar batch_size pequeño
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Configuracion
config = Configuracion.load()
config.batch_size = 3  # Procesar solo 3 tareas por ejecución
config.save()
print('batch_size configurado a 3')
"

# 2. Crear 10 tareas
#    - Desde Admin, 10 alumnos → Acción Teams

# 3. Primera ejecución del cron (debe procesar solo 3)
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.tasks import procesar_cola_tareas_pendientes
procesar_cola_tareas_pendientes()
from alumnos.models import Tarea
pending = Tarea.objects.filter(estado='pending').count()
running_or_done = Tarea.objects.exclude(estado='pending').count()
print(f'Procesadas: {running_or_done}')
print(f'Pendientes: {pending}')
"
# Debe mostrar: Procesadas=3, Pendientes=7
```

---

### Prueba 6: Acción "Eliminar solo de BD (sin tareas)"

```bash
# Crear alumnos de prueba
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Alumno
for i in range(5):
    Alumno.objects.create(
        tipo_documento='DNI',
        nro_documento=f'9999999{i}',
        apellido=f'Prueba{i}',
        nombre='Test',
        email=f'test{i}@example.com'
    )
print('5 alumnos de prueba creados')
"

# Desde Admin:
# - Seleccionar los 5 alumnos de prueba
# - Acción: "🗑️ Eliminar solo de BD (sin tareas asíncronas)"

# Verificar que se eliminaron SIN crear tareas
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Alumno, Tarea
pruebas = Alumno.objects.filter(apellido__startswith='Prueba').count()
tareas_elim = Tarea.objects.filter(tipo='eliminar_completo').count()
print(f'Alumnos de prueba restantes: {pruebas}')
print(f'Tareas de eliminación creadas: {tareas_elim}')
"
# Debe mostrar: pruebas=0, tareas_elim=0
```

---

## 📊 Dashboard de Monitoreo

### Ver estado del sistema en tiempo real

```bash
# Ver tareas pendientes por tipo
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Tarea
from collections import Counter
pending = Tarea.objects.filter(estado='pending')
tipos = Counter(t.tipo for t in pending)
print('=== Tareas PENDING por tipo ===')
for tipo, count in tipos.items():
    print(f'  {tipo}: {count}')
print(f'Total: {pending.count()}')
"

# Ver últimas 10 tareas procesadas
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Tarea
recientes = Tarea.objects.exclude(estado='pending').order_by('-hora_fin')[:10]
print('=== Últimas 10 tareas procesadas ===')
for t in recientes:
    print(f'{t.hora_fin}: {t.tipo} → {t.estado} ({t.alumno})')
"

# Ver logs del procesador
docker compose -f docker-compose.testing.yml logs -f celery | grep "\[Cola\]"
```

---

## 🔧 Comandos Útiles

```bash
# Reiniciar todo
docker compose -f docker-compose.testing.yml down
docker compose -f docker-compose.testing.yml up -d

# Ver logs en tiempo real
docker compose -f docker-compose.testing.yml logs -f web celery celery-beat

# Limpiar TODAS las tareas de prueba
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Tarea
Tarea.objects.all().delete()
print('Todas las tareas eliminadas')
"

# Editar tareas periódicas desde Admin
# http://localhost:8001/admin/django_celery_beat/periodictask/

# Editar configuración (batch_size, rate_limits)
# http://localhost:8001/admin/alumnos/configuracion/
```

---

## ✅ Checklist de Verificación

- [ ] Tareas periódicas creadas en Admin
- [ ] Celery Beat usa DatabaseScheduler
- [ ] Modo LEGACY funciona (ejecución inmediata)
- [ ] Modo QUEUE funciona (encolado)
- [ ] Rate limiting funciona (delays entre tareas)
- [ ] Batch size funciona (procesa en lotes)
- [ ] Acción "Eliminar solo BD" NO crea tareas
- [ ] Admin muestra solo Periodic tasks y Crontab schedules
- [ ] Logs del procesador muestran progreso

---

## 🚨 Troubleshooting

### Problema: "No se procesan las tareas pendientes"
```bash
# Verificar que celery-beat está corriendo
docker compose -f docker-compose.testing.yml ps celery-beat

# Ver logs de celery-beat
docker compose -f docker-compose.testing.yml logs celery-beat | tail -50

# Forzar ejecución manual
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.tasks import procesar_cola_tareas_pendientes
procesar_cola_tareas_pendientes()
"
```

### Problema: "Las tareas se ejecutan inmediatamente aunque USE_QUEUE_SYSTEM=true"
```bash
# Verificar que la variable se leyó correctamente
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django.conf import settings
print('USE_QUEUE_SYSTEM:', settings.USE_QUEUE_SYSTEM)
"

# Si muestra False, reiniciar servicios
docker compose -f docker-compose.testing.yml restart web celery celery-beat
```

### Problema: "Tareas periódicas no aparecen en Admin"
```bash
# Verificar que django-celery-beat está instalado
docker compose -f docker-compose.testing.yml exec web pip list | grep celery

# Verificar que las tablas existen
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
print('Tabla existe:', PeriodicTask.objects.exists())
"
```
