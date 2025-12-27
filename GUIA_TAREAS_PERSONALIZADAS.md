# 📘 Guía: Crear Tareas Periódicas Personalizadas

## 🎯 Flujo Completo: De Abajo hacia Arriba

### **Paso 1: Crear el Horario (Crontab)**

1. Ve a: **Admin → Tareas Periódicas → Crontabs → + Agregar**

2. Configura el horario según necesites:

#### **Ejemplo A: Todos los domingos a las 9 AM**
```
Minute: 0
Hour: 9
Day of week: 0  ← (0 = Domingo, 6 = Sábado)
Day of month: *
Month of year: *
Timezone: America/Argentina/Cordoba
```

#### **Ejemplo B: Último día de cada mes a las 23:00**
```
Minute: 0
Hour: 23
Day of week: *
Day of month: 28-31  ← (últimos días)
Month of year: *
Timezone: America/Argentina/Cordoba
```

#### **Ejemplo C: Primer lunes de cada mes a las 8 AM**
```
Minute: 0
Hour: 8
Day of week: 1  ← (Lunes)
Day of month: 1-7  ← (primera semana)
Month of year: *
Timezone: America/Argentina/Cordoba
```

#### **Ejemplo D: Cada 30 minutos**
```
Minute: */30
Hour: *
Day of week: *
Day of month: *
Month of year: *
Timezone: America/Argentina/Cordoba
```

3. **Guardar** → Anota el ID o descripción del crontab creado

---

### **Paso 2: Elegir o Crear la Tarea**

Tienes **3 opciones**:

---

#### **Opción A: Usar Tarea Existente** ✅ (Más fácil)

Si la tarea ya existe en el código, simplemente:

1. Ve a: **Admin → Tareas Periódicas → Tareas periódicas → + Agregar**
2. Rellena:
   ```
   Name: Nombre descriptivo de tu tarea
   Task (registered): [Selecciona del dropdown]
   Enabled: ✓
   Crontab Schedule: [Selecciona el crontab que creaste]
   Description: Qué hace esta tarea
   ```
3. Guardar

**Tareas disponibles actualmente:**
- `alumnos.tasks.procesar_cola_tareas_pendientes`
- `alumnos.tasks.ingestar_preinscriptos`
- `alumnos.tasks.ingestar_aspirantes`
- `alumnos.tasks.ingestar_ingresantes`
- `alumnos.tasks.procesar_lote_alumnos_nuevos`
- `alumnos.tasks.tarea_personalizada_ejemplo` ← **NUEVA (ejemplo)**
- Y todas las demás que viste en el dropdown

---

#### **Opción B: Crear Tarea Personalizada** 🔧 (Para desarrolladores)

Si necesitas ejecutar **código personalizado**:

##### **1. Edita el archivo de tareas:**

```bash
# Editar tasks.py
nano /home/carlos/work/pylucy/src/alumnos/tasks.py
```

##### **2. Agrega tu tarea al final del archivo:**

```python
@shared_task(bind=True)
def mi_reporte_semanal(self):
    """
    Genera un reporte semanal de alumnos ingresantes.
    Se ejecuta todos los domingos.
    """
    logger.info("📊 Generando reporte semanal")

    try:
        from .models import Alumno
        from datetime import timedelta
        from django.utils import timezone

        # Contar alumnos de la última semana
        hace_una_semana = timezone.now() - timedelta(days=7)
        nuevos = Alumno.objects.filter(
            fecha_creacion__gte=hace_una_semana
        ).count()

        logger.info(f"📈 Nuevos alumnos esta semana: {nuevos}")

        # Aquí podrías:
        # - Generar un archivo CSV
        # - Enviar email con el reporte
        # - Guardar en la BD
        # - Crear un Log

        return {
            'success': True,
            'nuevos_alumnos': nuevos,
            'periodo': 'última semana'
        }

    except Exception as e:
        logger.error(f"❌ Error generando reporte: {e}")
        return {
            'success': False,
            'error': str(e)
        }
```

##### **3. Reinicia Celery:**

```bash
docker compose -f docker-compose.testing.yml restart celery celery-beat
```

##### **4. Ahora crea la tarea periódica:**

1. Ve a: **Admin → Tareas Periódicas → Tareas periódicas → + Agregar**
2. Rellena:
   ```
   Name: Reporte Semanal de Ingresos
   Task (registered): alumnos.tasks.mi_reporte_semanal  ← Tu tarea nueva
   Enabled: ✓
   Crontab Schedule: [El de domingos 9 AM]
   Description: Genera reporte semanal todos los domingos
   ```
3. Guardar

---

#### **Opción C: Tarea de Sistema/Django** ⚙️ (Avanzado)

Para ejecutar comandos de Django o tareas del sistema:

```python
@shared_task
def ejecutar_comando_django():
    """
    Ejecuta un comando de Django management.
    """
    from django.core.management import call_command

    # Ejemplo: limpiar sesiones viejas
    call_command('clearsessions')

    # Ejemplo: crear backup
    # call_command('dumpdata', '--output=backup.json')

    return {'success': True}
```

---

## 📋 Referencia Rápida de Crontab

### Formato: `minute hour day_of_month month day_of_week`

| Expresión | Significado |
|-----------|-------------|
| `*/5 * * * *` | Cada 5 minutos |
| `0 * * * *` | Cada hora (en punto) |
| `0 9 * * *` | Todos los días a las 9 AM |
| `0 9 * * 1` | Todos los lunes a las 9 AM |
| `0 9 * * 0` | Todos los domingos a las 9 AM |
| `0 0 1 * *` | Primer día de cada mes a las 0:00 |
| `0 0 * * 0,6` | Sábados y domingos a las 0:00 |
| `*/15 9-17 * * 1-5` | Cada 15 min entre 9-17hs, lunes a viernes |

### Días de la semana:
- `0` = Domingo
- `1` = Lunes
- `2` = Martes
- `3` = Miércoles
- `4` = Jueves
- `5` = Viernes
- `6` = Sábado

---

## 🧪 Probar una Tarea Manualmente

Antes de programarla, puedes ejecutarla manualmente:

```bash
# Entrar al shell de Django
docker compose -f docker-compose.testing.yml exec web python manage.py shell

# Ejecutar la tarea
>>> from alumnos.tasks import mi_reporte_semanal
>>> resultado = mi_reporte_semanal()
>>> print(resultado)
```

O desde Celery:

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.tasks import tarea_personalizada_ejemplo
resultado = tarea_personalizada_ejemplo.delay()
print('Task ID:', resultado.id)
print('Estado:', resultado.status)
"
```

---

## 📊 Monitorear Tareas Programadas

### Ver próximas ejecuciones:

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
from django.utils import timezone

print('=== PRÓXIMAS EJECUCIONES ===')
for task in PeriodicTask.objects.filter(enabled=True):
    print(f'{task.name}:')
    print(f'  Schedule: {task.crontab or task.interval}')
    print(f'  Last run: {task.last_run_at or \"Nunca\"}')
    print()
"
```

### Ver logs de ejecuciones:

```bash
# Logs de Celery Beat (scheduler)
docker compose -f docker-compose.testing.yml logs -f celery-beat | grep "Scheduler"

# Logs de Celery Worker (ejecutor)
docker compose -f docker-compose.testing.yml logs -f celery | grep "mi_tarea"
```

---

## 🎯 Casos de Uso Comunes

### **1. Reporte Diario por Email**

```python
@shared_task(bind=True)
def enviar_reporte_diario(self):
    """Envía reporte diario a administradores."""
    from .services.email_service import EmailService
    from .models import Alumno

    total = Alumno.objects.count()
    activos = Alumno.objects.filter(activo=True).count()

    mensaje = f"""
    Reporte Diario - {timezone.now().date()}

    Total alumnos: {total}
    Alumnos activos: {activos}
    """

    EmailService.enviar_email_simple(
        destinatario='admin@eco.unrc.edu.ar',
        asunto='Reporte Diario PyLucy',
        mensaje=mensaje
    )
```

**Crontab**: `0 8 * * *` (todos los días a las 8 AM)

---

### **2. Limpieza Semanal de Logs**

```python
@shared_task(bind=True)
def limpiar_logs_antiguos(self):
    """Elimina logs de más de 30 días."""
    from .models import Log
    from datetime import timedelta

    hace_30_dias = timezone.now() - timedelta(days=30)
    eliminados = Log.objects.filter(
        fecha__lt=hace_30_dias
    ).delete()

    logger.info(f"🗑️ Logs eliminados: {eliminados[0]}")
    return {'eliminados': eliminados[0]}
```

**Crontab**: `0 2 * * 0` (domingos a las 2 AM)

---

### **3. Recordatorio Mensual**

```python
@shared_task(bind=True)
def recordatorio_mensual(self):
    """Envía recordatorio el primer día de cada mes."""
    logger.info("📅 Enviando recordatorio mensual")
    # Tu código aquí
```

**Crontab**: `0 9 1 * *` (día 1 de cada mes a las 9 AM)

---

## ⚠️ Buenas Prácticas

1. **Siempre usa `@shared_task(bind=True)`** para acceso al contexto
2. **Agrega logging** para debug (`logger.info()`, `logger.error()`)
3. **Maneja excepciones** con try/except
4. **Retorna un dict** con `success` y detalles
5. **Documenta la tarea** (docstring)
6. **Prueba manualmente** antes de programar
7. **Usa `timezone.now()`** en vez de `datetime.now()`
8. **No bloquees el worker** (evita loops infinitos, sleep largos)

---

## 🔍 Troubleshooting

### "Mi tarea no aparece en el dropdown"
```bash
# Reiniciar Celery
docker compose -f docker-compose.testing.yml restart celery celery-beat

# Verificar que se cargó
docker compose -f docker-compose.testing.yml logs celery | grep "alumnos.tasks"
```

### "La tarea no se ejecuta"
```bash
# Ver si está habilitada
# Admin → Tareas periódicas → verificar Enabled=True

# Ver logs de celery-beat
docker compose -f docker-compose.testing.yml logs celery-beat | tail -50
```

### "Error al ejecutar la tarea"
```bash
# Ver logs del worker
docker compose -f docker-compose.testing.yml logs celery | grep ERROR

# Ver tabla de Tareas Asíncronas en el admin
# Admin → Tareas Asíncronas → buscar tu tarea → ver mensaje_error
```

---

## 📚 Recursos

- **Crontab.guru**: https://crontab.guru/ (generador visual de crontabs)
- **Celery Docs**: https://docs.celeryq.dev/
- **Django-Celery-Beat**: https://django-celery-beat.readthedocs.io/

---

## ✅ Checklist de Creación

- [ ] Crear crontab con el horario deseado
- [ ] Crear tarea en `tasks.py` (si es personalizada)
- [ ] Reiniciar Celery
- [ ] Crear tarea periódica en Admin
- [ ] Asignar crontab a la tarea
- [ ] Habilitar la tarea (Enabled=True)
- [ ] Probar manualmente
- [ ] Verificar en logs que se ejecuta
