# 📋 Documentación: update-cron.sh

## 🎯 Propósito

Script para configurar tareas periódicas de Celery Beat y cargar valores por defecto de configuración en entornos Docker de PyLucy (testing/producción).

## 📦 ¿Qué hace el script?

1. ✅ **Aplica migraciones pendientes** (incluida `rate_limit_uti`)
2. ✅ **Configura 3 tareas periódicas** en Celery Beat
3. ✅ **Carga valores por defecto** de configuración
4. ✅ **Reinicia Celery Beat** para aplicar cambios
5. ✅ **Muestra estado** de tareas y configuración

---

## 🚀 Ejecución Documentada

### **Paso 1: Verificar contenedores**

```bash
docker compose -f docker-compose.testing.yml ps
```

**Output esperado**:
```
NAME                          STATUS
pylucy-web-testing            Up X minutes
pylucy-celery-testing         Up X minutes
pylucy-celery-beat-testing    Up X minutes
pylucy-db-testing             Up X minutes (healthy)
pylucy-redis-testing          Up X minutes (healthy)
```

### **Paso 2: Ejecutar script**

```bash
./update-cron.sh testing
```

**Output documentado**:

```
[INFO] Entorno: TESTING

============================================
  PyLucy - Configurar Cron/Celery Beat
  Entorno: testing
============================================

[INFO] Aplicando migraciones pendientes...
Operations to perform:
  Apply all migrations: admin, alumnos, auth, contenttypes, cursos, django_celery_beat, sessions
Running migrations:
  Applying alumnos.0022_add_rate_limit_uti... OK
[✓] Migraciones aplicadas

[INFO] Configurando tareas periódicas de Celery Beat...
✓ Tarea 'ingesta-preinscriptos': creada (intervalo: 3600s, habilitada: False)
✓ Tarea 'ingesta-aspirantes': creada (intervalo: 3600s, habilitada: False)
✓ Tarea 'ingesta-ingresantes': creada (intervalo: 3600s, habilitada: False)

✅ Tareas periódicas configuradas correctamente
[✓] Tareas periódicas configuradas

[INFO] Verificando configuración del sistema...
✓ rate_limit_uti: 60/min

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFIGURACIÓN ACTUAL:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Batch size: 20
Rate limit Teams: 10/min
Rate limit Moodle: 30/min
Rate limit UTI: 60/min

Ingesta Preinscriptos:
  Inicio: No configurado
  Fin: Sin límite
  Frecuencia: 3600s

Ingesta Aspirantes:
  Inicio: No configurado
  Fin: Sin límite
  Frecuencia: 3600s

Ingesta Ingresantes:
  Inicio: No configurado
  Fin: Sin límite
  Frecuencia: 3600s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[✓] Configuración verificada

[INFO] Reiniciando Celery Beat...
[✓] Celery Beat reiniciado

[INFO] Tareas periódicas registradas:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TAREAS PERIÓDICAS EN CELERY BEAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Habilitada | celery.backend_cleanup
          Task: celery.backend_cleanup
          Intervalo: N/A

⏸️  Deshabilitada | ingesta-preinscriptos
          Task: alumnos.tasks.ingestar_preinscriptos
          Intervalo: cada 3600seconds

⏸️  Deshabilitada | ingesta-aspirantes
          Task: alumnos.tasks.ingestar_aspirantes
          Intervalo: cada 3600seconds

⏸️  Deshabilitada | ingesta-ingresantes
          Task: alumnos.tasks.ingestar_ingresantes
          Intervalo: cada 3600seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[✓] ¡Configuración de Cron/Celery Beat completada exitosamente!
```

### **Paso 3: Verificar configuración**

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell
```

```python
from django_celery_beat.models import PeriodicTask
from alumnos.models import Configuracion

# Verificar rate limits
config = Configuracion.load()
print(f"Rate limit UTI: {config.rate_limit_uti}/min")  # Output: 60/min
print(f"Rate limit Teams: {config.rate_limit_teams}/min")  # Output: 10/min
print(f"Rate limit Moodle: {config.rate_limit_moodle}/min")  # Output: 30/min

# Verificar tareas periódicas
for task in PeriodicTask.objects.filter(task__startswith='alumnos'):
    print(f"{task.name}: {'✅ Habilitada' if task.enabled else '⏸️  Deshabilitada'}")
```

**Output esperado**:
```
Rate limit UTI: 60/min
Rate limit Teams: 10/min
Rate limit Moodle: 30/min
ingesta-preinscriptos: ⏸️  Deshabilitada
ingesta-aspirantes: ⏸️  Deshabilitada
ingesta-ingresantes: ⏸️  Deshabilitada
```

---

## 📊 Tareas Creadas

| Nombre | Task | Intervalo Default | Estado Inicial |
|--------|------|-------------------|----------------|
| `ingesta-preinscriptos` | `alumnos.tasks.ingestar_preinscriptos` | 3600s (1h) | ⏸️ Deshabilitada |
| `ingesta-aspirantes` | `alumnos.tasks.ingestar_aspirantes` | 3600s (1h) | ⏸️ Deshabilitada |
| `ingesta-ingresantes` | `alumnos.tasks.ingestar_ingresantes` | 3600s (1h) | ⏸️ Deshabilitada |

**Nota**: Las tareas están DESHABILITADAS por defecto. Se habilitan automáticamente cuando se configura `*_dia_inicio` en la BD.

---

## 🔧 Valores por Defecto Cargados

```python
{
    "batch_size": 20,           # Alumnos por lote
    "rate_limit_teams": 10,     # Llamadas/min a Teams
    "rate_limit_moodle": 30,    # Llamadas/min a Moodle
    "rate_limit_uti": 60,       # Llamadas/min a API UTI (NUEVO)

    # Frecuencias de ingesta (segundos)
    "preinscriptos_frecuencia_segundos": 3600,  # Cada 1 hora
    "aspirantes_frecuencia_segundos": 3600,     # Cada 1 hora
    "ingresantes_frecuencia_segundos": 3600,    # Cada 1 hora
}
```

---

## 🌐 Habilitar Ingestas Automáticas

### **Opción A: Django Admin** (recomendado)

1. Ir a: `http://localhost:8000/admin/alumnos/configuracion/`
2. Configurar:
   ```
   Preinscriptos día inicio: 2025-12-17 00:00:00
   Preinscriptos día fin: 2026-03-01 00:00:00  (opcional)
   ```
3. Guardar
4. **Reiniciar Celery Beat**:
   ```bash
   docker compose -f docker-compose.testing.yml restart celery-beat
   ```

### **Opción B: Django Shell**

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell
```

```python
from alumnos.models import Configuracion
from datetime import datetime
from django.utils import timezone

config = Configuracion.load()
config.preinscriptos_dia_inicio = timezone.now()
config.save()
```

**Luego reiniciar Celery Beat**:
```bash
docker compose -f docker-compose.testing.yml restart celery-beat
```

### **Opción C: Volver a ejecutar script**

```bash
./update-cron.sh testing
```

---

## 🔍 Verificar que Funcione

### **1. Ver logs de Celery Beat**

```bash
docker compose -f docker-compose.testing.yml logs -f celery-beat
```

**Deberías ver** (cuando las tareas estén habilitadas):
```
[INFO] Scheduler: Sending due task ingesta-preinscriptos
[INFO] Scheduler: Sending due task ingesta-aspirantes
```

### **2. Ver logs de Celery Worker**

```bash
docker compose -f docker-compose.testing.yml logs -f celery
```

**Deberías ver**:
```
[INFO] Task alumnos.tasks.ingestar_preinscriptos[<id>] received
[INFO] [Ingesta Auto-Preinscriptos] Iniciando ingesta automática de preinscriptos
[INFO] [Ingesta Auto-Preinscriptos] ✅ Finalizada: 45 creados, 12 actualizados
```

### **3. Ver en Django Admin**

- **Tareas periódicas**: http://localhost:8000/admin/django_celery_beat/periodictask/
- **Historial de ejecución**: http://localhost:8000/admin/alumnos/tarea/
- **Logs del sistema**: http://localhost:8000/admin/alumnos/log/

---

## 🚨 Troubleshooting

### **Problema: "Tareas no se ejecutan"**

**Verificar**:
1. ¿Está configurado `*_dia_inicio`?
   ```bash
   docker compose -f docker-compose.testing.yml exec web python manage.py shell
   ```
   ```python
   from alumnos.models import Configuracion
   config = Configuracion.load()
   print(config.preinscriptos_dia_inicio)  # ¿Es None?
   ```

2. ¿Está habilitada la tarea?
   ```python
   from django_celery_beat.models import PeriodicTask
   task = PeriodicTask.objects.get(name='ingesta-preinscriptos')
   print(task.enabled)  # ¿Es False?
   ```

3. ¿Está corriendo Celery Beat?
   ```bash
   docker compose -f docker-compose.testing.yml ps celery-beat
   ```

### **Problema: "Column rate_limit_uti does not exist"**

**Solución**:
```bash
# Crear migración
docker compose -f docker-compose.testing.yml exec web python manage.py makemigrations alumnos

# Aplicar migración
docker compose -f docker-compose.testing.yml exec web python manage.py migrate

# Ejecutar script nuevamente
./update-cron.sh testing
```

---

## 📝 Para Servidor Remoto (Producción)

### **1. En servidor local (desarrollo)**

```bash
# Hacer commit de todos los cambios
git add .
git commit -m "feat: Agregar rate_limit_uti y mejorar sistema de logs

- Nuevo campo rate_limit_uti en Configuracion
- Logs categorizados (UTI, datos, correo, guardado)
- Ingesta manual ahora va a cola de Celery
- Plantillas de email desde BD
- Script update-cron.sh para configurar tareas periódicas"

# Hacer push
git push origin main
```

### **2. En servidor remoto (producción)**

```bash
# Hacer pull
git pull origin main

# Ejecutar update-testing-prod.sh (aplica migraciones y reinicia)
./update-testing-prod.sh prod

# Configurar cron/celery beat
./update-cron.sh prod
```

---

## 📄 Archivos Relacionados

| Archivo | Descripción |
|---------|-------------|
| `update-cron.sh` | Script principal de configuración |
| `update-testing-prod.sh` | Script de actualización de código |
| `src/alumnos/migrations/0022_add_rate_limit_uti.py` | Migración generada |
| `src/alumnos/management/commands/config.py` | Comando para exportar/importar config |

---

## ✅ Checklist Post-Ejecución

- [ ] Migración `0022_add_rate_limit_uti` aplicada
- [ ] 3 tareas periódicas creadas en BD
- [ ] `rate_limit_uti` configurado (default: 60/min)
- [ ] Celery Beat reiniciado correctamente
- [ ] Logs muestran "DatabaseScheduler"
- [ ] Tareas visibles en Django Admin

---

## 📊 Estado Final Esperado

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell
```

```python
from django_celery_beat.models import PeriodicTask
from alumnos.models import Configuracion

config = Configuracion.load()
print(f"✅ rate_limit_uti: {config.rate_limit_uti}/min")

tasks = PeriodicTask.objects.filter(task__startswith='alumnos')
print(f"✅ Tareas creadas: {tasks.count()}")  # Debe ser 3
```

**Output esperado**:
```
✅ rate_limit_uti: 60/min
✅ Tareas creadas: 3
```

---

**Fecha de ejecución documentada**: 2025-12-17
**Entorno**: Testing (Docker)
**Usuario**: Carlos
**Estado**: ✅ Éxito completo
