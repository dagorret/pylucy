# ❓ FAQ: Ingesta y Configuración de Emails

## Pregunta 1: ¿Cómo funciona el "desde/hasta" en la ingesta de preinscriptos?

### 📊 Estado Actual

**✅ IMPLEMENTADO**: La ingesta automática de preinscriptos, aspirantes e ingresantes **AHORA USA consulta incremental**.

Cuando las tareas automáticas se ejecutan:

```python
# En tasks.py - Ejemplo de ingestar_preinscriptos
desde = None
hasta = ahora.isoformat()

if config.ultima_ingesta_preinscriptos:
    desde = (config.ultima_ingesta_preinscriptos + timedelta(seconds=1)).isoformat()
    logger.info(f"[Ingesta Incremental] Desde: {desde}, Hasta: {hasta}")
else:
    logger.info("[Ingesta Completa] Primera ejecución, trayendo lista completa")

ingerir_desde_sial(
    tipo='preinscriptos',
    desde=desde,
    hasta=hasta,
    retornar_nuevos=True,
    enviar_email=enviar_email
)

# Actualizar timestamp tras éxito
config.ultima_ingesta_preinscriptos = ahora
config.save(update_fields=['ultima_ingesta_preinscriptos'])
```

### Comportamiento Actual:
```
PRIMERA EJECUCIÓN:
  API UTI llamada: /webservice/sial/V2/04/preinscriptos/listas/
  Resultado: Trae TODA la lista completa
  Timestamp guardado: 2025-12-27T10:00:00

SIGUIENTES EJECUCIONES:
  API UTI llamada: /listas/2025-12-27T10:00:01/2025-12-27T10:05:00
  Resultado: Solo registros modificados entre esas fechas
  Timestamp actualizado: 2025-12-27T10:05:00
```

### ✅ Ventajas:
- Mucho más eficiente (menos datos transferidos)
- Menos carga en API UTI
- Procesamiento más rápido
- Solo trae cambios desde última ejecución exitosa

---

## ✅ Implementación Completada

### ¿Qué se implementó?

1. **Consulta Incremental Automática**:
   - Agregados 3 campos en `Configuracion`: `ultima_ingesta_preinscriptos`, `ultima_ingesta_aspirantes`, `ultima_ingesta_ingresantes`
   - Modificadas las 3 tareas automáticas para usar consulta incremental
   - Los timestamps se actualizan automáticamente tras cada ejecución exitosa
   - Primera ejecución trae lista completa, siguientes traen solo cambios

2. **Ingesta Manual con Desde/Hasta**:
   - Ya existía en **Admin → Alumnos → Consumir**
   - Ubicación: `/admin/alumnos/alumno/ingesta/`
   - Formulario para elegir tipo, desde, hasta y envío de emails
   - Va por sistema de colas (usa `ingesta_manual_task.delay()`)

3. **Migración Aplicada**:
   - Migración `0028_remove_alumno_email_payload_and_more.py`
   - Campos creados en base de datos
   - Servicios reiniciados y funcionando

---

## 📥 Cómo Usar la Ingesta Manual (Botón "Consumir" en Alumnos)

### Acceder:
1. **Admin → Alumnos**
2. En la interfaz de listado de alumnos verás el botón **"Consumir"**
3. O ir directo a: `http://localhost:8001/admin/alumnos/alumno/ingesta/`

### Formulario:
- **Tipo**: Elegir preinscriptos, aspirantes o ingresantes
- **Desde** (opcional): Fecha/hora de inicio
- **Hasta** (opcional): Fecha/hora de fin
- **Enviar emails**: Checkbox para controlar envío
- **N** (opcional): Cantidad de registros (para testing)
- **Seed** (opcional): Semilla aleatoria (para testing)

### Casos de Uso:

**📋 Lista Completa** (reprocesar todo):
```
Action: consume
Tipo: preinscriptos
Desde: [vacío]
Hasta: [vacío]
Enviar emails: ☐ (desmarcar si no quieres enviar)
```

**🔍 Rango Específico** (recuperar datos de un período):
```
Action: consume
Tipo: aspirantes
Desde: 2025-12-01T00:00:00
Hasta: 2025-12-31T23:59:59
Enviar emails: ☑ (marcar si quieres reenviar)
```

**⚡ Solo últimas horas**:
```
Action: consume
Tipo: ingresantes
Desde: 2025-12-27T10:00:00
Hasta: 2025-12-27T12:00:00
Enviar emails: ☑/☐ (según necesidad)
```

**Nota**: La tarea se encola en el sistema de colas y se procesa asíncronamente. Revisa el resultado en **Admin → Tareas Asíncronas**.

---

## Pregunta 2: ¿Cómo se configura el envío de email (con/sin email de bienvenida)?

### 📋 Respuesta: Sale de Configuración del Sistema

**No es una tarea separada**. Es un **parámetro de configuración** en la base de datos.

### 🔧 Dónde se configura:

**Admin → Configuración del Sistema → Sección "Ingesta de Preinscriptos"**

Hay un campo:
```
☑️ Enviar email de bienvenida a preinscriptos durante ingesta automática
```

### 📁 En la Base de Datos:

**Tabla**: `alumnos_configuracion`
**Campo**: `preinscriptos_enviar_email`
**Tipo**: Boolean (True/False)
**Default**: `True`

### 💻 En el Código:

**Modelo** (`src/alumnos/models.py`):
```python
class Configuracion(models.Model):
    preinscriptos_enviar_email = models.BooleanField(
        default=True,
        help_text="✉️ Enviar email de bienvenida a preinscriptos durante ingesta automática"
    )
```

**Tarea** (`src/alumnos/tasks.py` línea 52-54):
```python
# Leer configuración de email
enviar_email = config.preinscriptos_enviar_email
logger.info(f"[Ingesta Auto-Preinscriptos] Enviar email: {enviar_email}")

# Pasar a la función de ingesta
created, updated, errors, nuevos_ids = ingerir_desde_sial(
    tipo='preinscriptos',
    retornar_nuevos=True,
    enviar_email=enviar_email  # ← Aquí se pasa
)
```

### 🎯 Cómo funciona:

1. **La tarea lee** el campo de configuración cada vez que se ejecuta
2. **Pasa el parámetro** `enviar_email=True/False` a `ingerir_desde_sial()`
3. **La función de ingesta** decide si enviar email según ese parámetro

### ⚙️ Cambiar el comportamiento:

**Opción A: Desde el Admin (RECOMENDADO)**
```
1. Admin → Configuración del Sistema
2. Editar el único registro
3. Marcar/desmarcar "Enviar email de bienvenida..."
4. Guardar
```

**Opción B: Desde el shell**
```python
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Configuracion
config = Configuracion.load()
config.preinscriptos_enviar_email = False  # Desactivar emails
config.save()
print('✅ Emails desactivados para preinscriptos')
"
```

---

## 📊 Campos Similares en Configuración

Cada tipo de ingesta tiene su campo:

| Campo | Descripción |
|-------|-------------|
| `preinscriptos_enviar_email` | ✉️ Email para preinscriptos |
| `aspirantes_enviar_email` | ✉️ Email para aspirantes |
| `ingresantes_enviar_email` | ✉️ Email para ingresantes |

**Todos** funcionan igual: se leen de configuración en cada ejecución.

---

## 🔄 Flujo Completo

```
┌─────────────────────────────────────┐
│ Celery Beat: cada 5 minutos         │
└───────────┬─────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ Tarea: ingestar_preinscriptos()     │
│ 1. Verifica horario configurado     │
│ 2. Lee config.preinscriptos_enviar  │
└───────────┬─────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ Función: ingerir_desde_sial()       │
│ 1. Llama API UTI                    │
│ 2. Procesa registros                │
│ 3. update_or_create()               │
│ 4. Si enviar_email=True → envía    │
└─────────────────────────────────────┘
```

---

## ✅ Resumen de Respuestas

### **Pregunta 1: ¿Cómo funciona desde/hasta?**
**Respuesta**:
- ✅ **IMPLEMENTADO**: Ahora usa consulta incremental automáticamente
- ✅ Trae solo cambios desde última ejecución exitosa
- ✅ Primera ejecución trae lista completa, siguientes son incrementales
- ✅ Timestamps guardados en `Configuracion.ultima_ingesta_*`
- ✅ También disponible **ingesta manual** con desde/hasta personalizados

### **Pregunta 2: ¿Cómo configurar con/sin email?**
**Respuesta**:
- ✅ Se configura en **Admin → Configuración del Sistema**
- ✅ Campos: `preinscriptos_enviar_email`, `aspirantes_enviar_email`, `ingresantes_enviar_email` (Boolean)
- ✅ Se aplica automáticamente en cada ejecución
- ✅ NO necesitas crear tareas separadas
- ✅ En ingesta manual también puedes controlarlo por ejecución

---

## 🎯 Próximos Pasos Recomendados

### ✅ Ya Implementado:
- Consulta incremental en ingestas automáticas
- Ingesta manual con desde/hasta en Admin
- Sistema de timestamps para tracking

### Para usar el sistema:
1. **Ingesta Automática**: Se ejecuta cada 5 minutos con consulta incremental
2. **Ingesta Manual**: Admin → Alumnos → Botón "Consumir"
3. **Configurar emails**: Admin → Configuración → Campos `*_enviar_email`
4. **Monitorear**: Admin → Tareas Asíncronas (ver resultados y errores)

### Para verificar que funciona:
```bash
# Ver logs de celery
docker compose -f docker-compose.testing.yml logs -f celery

# Ver timestamps actuales
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Configuracion
c = Configuracion.load()
print(f'Preinscriptos: {c.ultima_ingesta_preinscriptos}')
print(f'Aspirantes: {c.ultima_ingesta_aspirantes}')
print(f'Ingresantes: {c.ultima_ingesta_ingresantes}')
"
```

---

**Última actualización**: 2025-12-27 (Implementación completa)
