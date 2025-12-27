# 📚 Índice de Documentación: Sistema de Colas PyLucy

Este índice te guía a la documentación correcta según lo que necesites hacer.

---

## 🎯 Según Tu Necesidad

### **"Quiero entender cómo funciona el sistema"**
→ Lee: [`docs/ARQUITECTURA_COLAS.md`](docs/ARQUITECTURA_COLAS.md)
- Diagrama del flujo completo
- Cómo se procesan las tareas
- Batch size y rate limiting
- Configuración del sistema

---

### **"Quiero crear una tarea programada personalizada"**
→ Lee: [`GUIA_TAREAS_PERSONALIZADAS.md`](GUIA_TAREAS_PERSONALIZADAS.md)
- Flujo paso a paso (de abajo hacia arriba)
- Cómo crear crontabs
- Cómo escribir tareas en código
- Ejemplos de casos de uso
- Referencia de sintaxis crontab

---

### **"¿Qué hace cada tarea que aparece en el dropdown?"**
→ Lee: [`CATALOGO_TAREAS_PREDEFINIDAS.md`](CATALOGO_TAREAS_PREDEFINIDAS.md)
- Lista completa de todas las tareas
- Descripción detallada de cada una
- Cuáles ya están programadas
- Cuáles NO debes programar
- Categorización por tipo

---

### **"Quiero probar que el sistema funciona"**
→ Lee: [`PRUEBAS_SISTEMA_COLAS.md`](PRUEBAS_SISTEMA_COLAS.md)
- Cómo probar modo LEGACY
- Cómo probar modo QUEUE
- Verificar rate limiting
- Verificar batch size
- Comandos de troubleshooting

---

## 📖 Documentos Disponibles

| Documento | Descripción | Cuándo Leerlo |
|-----------|-------------|---------------|
| **ARQUITECTURA_COLAS.md** | Documentación técnica completa | Para entender el sistema |
| **CATALOGO_TAREAS_PREDEFINIDAS.md** | Catálogo de todas las tareas | Para saber qué hace cada tarea |
| **GUIA_TAREAS_PERSONALIZADAS.md** | Guía para crear tareas propias | Para programar tareas custom |
| **PRUEBAS_SISTEMA_COLAS.md** | Plan de pruebas y verificación | Para testing y validación |
| **INDICE_DOCUMENTACION_COLAS.md** | Este archivo | Punto de entrada |

---

## 🚀 Quick Start

### Si eres nuevo:
1. Lee **ARQUITECTURA_COLAS.md** (sección "Visión General")
2. Lee **CATALOGO_TAREAS_PREDEFINIDAS.md** (sección "Resumen")
3. Revisa el Admin: http://localhost:8001/admin/django_celery_beat/periodictask/

### Si quieres crear una tarea:
1. Lee **GUIA_TAREAS_PERSONALIZADAS.md** completa
2. Sigue el ejemplo de `tarea_personalizada_ejemplo` en `tasks.py`
3. Prueba manualmente antes de programar

### Si algo no funciona:
1. Lee **PRUEBAS_SISTEMA_COLAS.md** (sección "Troubleshooting")
2. Revisa logs: `docker compose logs celery celery-beat`
3. Verifica Admin → Tareas Asíncronas

---

## 🔑 Conceptos Clave

### **Crontab vs Tarea Periódica**
- **Crontab** = Horario (cuándo ejecutar)
- **Tarea** = Código (qué ejecutar)
- **Tarea Periódica** = Crontab + Tarea (cuándo + qué)

### **Modos de Operación**
- **LEGACY** (`USE_QUEUE_SYSTEM=false`): Ejecución inmediata con `.delay()`
- **QUEUE** (`USE_QUEUE_SYSTEM=true`): Encolado con procesamiento cada 5 min

### **Tipos de Tareas**
- ⏰ **Programables**: Se pueden/deben programar periódicamente
- 🔘 **Bajo demanda**: Solo por acciones del admin
- ⚙️ **Internas**: Ya configuradas automáticamente
- ⚠️ **Peligrosas**: Eliminaciones irreversibles

---

## 📊 Estado Actual del Sistema

### Tareas Periódicas Configuradas (5):
1. ✅ Procesador de Cola de Tareas → `*/5 * * * *`
2. ✅ Ingesta Automática de Preinscriptos → `*/5 * * * *`
3. ✅ Ingesta Automática de Aspirantes → `*/5 * * * *`
4. ✅ Ingesta Automática de Ingresantes → `*/5 * * * *`
5. ✅ celery.backend_cleanup → `0 4 * * *`

### Modo Actual:
- USE_QUEUE_SYSTEM: `false` (LEGACY)
- Para cambiar a QUEUE: Agrega `USE_QUEUE_SYSTEM=true` en `.env`

### Verificar Estado:
```bash
# Ver tareas configuradas
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
for t in PeriodicTask.objects.filter(enabled=True):
    print(f'{t.name}: {t.crontab}')
"

# Ver modo actual
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django.conf import settings
print('Modo:', 'QUEUE' if settings.USE_QUEUE_SYSTEM else 'LEGACY')
"
```

---

## 🆘 Ayuda Rápida

### Error: "Tarea no aparece en dropdown"
```bash
docker compose -f docker-compose.testing.yml restart celery celery-beat
```

### Error: "Tarea no se ejecuta"
1. Verifica que esté habilitada: Admin → Tareas periódicas → Enabled=True
2. Ver logs: `docker compose logs celery-beat`

### Error: "No puedo agregar tarea periódica"
- Asegúrate de estar en: `http://localhost:8001/admin/django_celery_beat/periodictask/add/`
- No en la vista de edición de Crontab

### Quiero cambiar el horario de una tarea
1. Admin → Tareas Periódicas → Crontabs → Editar el crontab
2. O crear un nuevo crontab y asignarlo a la tarea

---

## 📞 Contacto

Si tienes dudas:
1. Lee la documentación correspondiente arriba
2. Revisa los ejemplos en `GUIA_TAREAS_PERSONALIZADAS.md`
3. Consulta los logs de Celery
4. Revisa Admin → Tareas Asíncronas para ver errores

---

**Última actualización**: 2025-12-27
