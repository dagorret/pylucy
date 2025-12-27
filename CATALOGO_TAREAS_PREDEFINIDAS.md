# 📚 Catálogo de Tareas Predefinidas - PyLucy

Este documento describe **todas las tareas Celery disponibles** en PyLucy, qué hace cada una, cuándo usarlas, y si deberían programarse o no.

---

## 🎯 Leyenda de Categorías

| Símbolo | Significado |
|---------|-------------|
| ⏰ | **Tarea programable** - Se puede/debe programar periódicamente |
| 🔘 | **Tarea bajo demanda** - Se ejecuta por acciones del admin (NO programar) |
| ⚙️ | **Tarea interna** - Parte del sistema de colas (Ya configurada) |
| ⚠️ | **Tarea peligrosa** - Eliminaciones irreversibles |
| 🧪 | **Tarea de ejemplo/debug** - Para testing |

---

## ⚙️ TAREAS DEL SISTEMA DE COLAS

Estas tareas son **internas** del sistema y **ya están configuradas**. No necesitas programarlas manualmente.

### ✅ `alumnos.tasks.procesar_cola_tareas_pendientes`
**Categoría**: ⚙️ Tarea interna (YA CONFIGURADA)

**Qué hace**:
- Procesador principal del sistema de colas
- Toma tareas con `estado=PENDING` de la tabla `Tarea`
- Las ejecuta respetando `batch_size` y `rate_limits`
- Agrupa por tipo de tarea y aplica delays

**Cuándo se ejecuta**:
- ✅ **Ya programada**: Cada 5 minutos (`*/5 * * * *`)

**¿Programar?**: ❌ NO (ya está configurada automáticamente)

**Configuración**:
- `batch_size`: Admin → Configuración → batch_size
- `rate_limit_teams`: Admin → Configuración → rate_limit_teams
- `rate_limit_moodle`: Admin → Configuración → rate_limit_moodle

**Logs**:
```bash
docker compose -f docker-compose.testing.yml logs celery | grep "\[Cola\]"
```

---

## 📥 TAREAS DE INGESTA (API UTI/SIAL)

Estas tareas sincronizan datos desde el sistema UTI/SIAL de la universidad.

### ✅ `alumnos.tasks.ingestar_preinscriptos`
**Categoría**: ⏰ Tarea programable (YA CONFIGURADA)

**Qué hace**:
- Consulta API UTI/SIAL para obtener preinscriptos con **consulta incremental**
- Verifica horario configurado en BD antes de ejecutar
- Solo ejecuta si está dentro del rango de fechas configurado
- Primera ejecución trae lista completa, siguientes traen solo cambios
- Actualiza timestamp `ultima_ingesta_preinscriptos` tras éxito
- Crea/actualiza registros de alumnos preinscriptos

**Cuándo se ejecuta**:
- ✅ **Ya programada**: Cada 5 minutos (`*/5 * * * *`)
- ⚙️ Verifica internamente: `preinscriptos_dia_inicio` y `preinscriptos_dia_fin`

**¿Programar?**: ❌ NO (ya está configurada)

**Configuración**:
- Admin → Configuración → Sección "Ingesta de Preinscriptos"
- `preinscriptos_dia_inicio`: Fecha inicio (ej: 01/12/2025)
- `preinscriptos_dia_fin`: Fecha fin (ej: 15/12/2025)
- `preinscriptos_enviar_email`: Boolean para enviar emails
- `ultima_ingesta_preinscriptos`: Timestamp de última ingesta (auto-gestionado)

**Ejemplo de configuración para ingesta de diciembre**:
```
Día inicio: 01/12/2025 08:00
Día fin: 15/12/2025 20:00
Enviar email: True/False
```
→ Solo ejecutará entre esas fechas/horas, aunque el cron corre cada 5 min.

**Consulta Incremental**:
- Primera ejecución: Trae `/listas/` completo
- Siguientes: Trae `/listas/{ultima+1s}/{ahora}` (solo cambios)

---

### ✅ `alumnos.tasks.ingestar_aspirantes`
**Categoría**: ⏰ Tarea programable (YA CONFIGURADA)

**Qué hace**:
- Consulta API UTI/SIAL para obtener aspirantes con **consulta incremental**
- Verifica horario configurado antes de ejecutar
- Primera ejecución trae lista completa, siguientes traen solo cambios
- Actualiza timestamp `ultima_ingesta_aspirantes` tras éxito
- Crea/actualiza registros de aspirantes

**Cuándo se ejecuta**:
- ✅ **Ya programada**: Cada 5 minutos (`*/5 * * * *`)
- ⚙️ Verifica internamente: `aspirantes_dia_inicio` y `aspirantes_dia_fin`

**¿Programar?**: ❌ NO (ya está configurada)

**Configuración**: Similar a preinscriptos, ver Admin → Configuración
**Consulta Incremental**: Trae `/listas/{ultima+1s}/{ahora}` (solo cambios)

---

### ✅ `alumnos.tasks.ingestar_ingresantes`
**Categoría**: ⏰ Tarea programable (YA CONFIGURADA)

**Qué hace**:
- Consulta API UTI/SIAL para obtener ingresantes con **consulta incremental**
- Verifica horario configurado antes de ejecutar
- Primera ejecución trae lista completa, siguientes traen solo cambios
- Actualiza timestamp `ultima_ingesta_ingresantes` tras éxito
- Crea/actualiza registros de ingresantes

**Cuándo se ejecuta**:
- ✅ **Ya programada**: Cada 5 minutos (`*/5 * * * *`)
- ⚙️ Verifica internamente: `ingresantes_dia_inicio` y `ingresantes_dia_fin`

**¿Programar?**: ❌ NO (ya está configurada)

**Configuración**: Similar a preinscriptos, ver Admin → Configuración
**Consulta Incremental**: Trae `/listas/{ultima+1s}/{ahora}` (solo cambios)

---

### `alumnos.tasks.ingesta_manual_task`
**Categoría**: 🔘 Tarea bajo demanda

**Qué hace**:
- Ingesta manual con parámetros `desde`/`hasta` personalizados
- NO verifica horarios configurados (ejecuta siempre)
- Permite especificar rango de fechas exacto
- Control sobre envío de emails por ejecución
- Va por sistema de colas (usa `.delay()`)

**Parámetros**:
- `tipo`: 'preinscriptos', 'aspirantes' o 'ingresantes'
- `desde`: Timestamp ISO inicio (opcional)
- `hasta`: Timestamp ISO fin (opcional)
- `enviar_email`: Boolean para enviar emails
- `n`: Cantidad de registros (opcional, para testing)
- `seed`: Semilla aleatoria (opcional, para testing)

**Casos de uso**:
- Lista completa: `desde=None, hasta=None`
- Rango específico: `desde='2025-12-01T00:00:00', hasta='2025-12-31T23:59:59'`
- Últimas horas: `desde='2025-12-27T10:00:00', hasta='2025-12-27T12:00:00'`

**¿Programar?**: ❌ NO (es para uso manual)

**Cómo ejecutar**:
1. **Admin → Alumnos** (en el listado de alumnos)
2. Busca el botón **"Consumir"**
3. O ir a: `/admin/alumnos/alumno/ingesta/`
4. Completar formulario:
   - Seleccionar `action=consume`
   - Tipo: preinscriptos/aspirantes/ingresantes
   - Desde/Hasta (opcional)
   - Checkbox enviar_email
5. Submit

**Monitoreo**: Admin → Tareas Asíncronas (ver resultado)

---

## 👤 TAREAS DE GESTIÓN DE ALUMNOS

Estas tareas se ejecutan **automáticamente** cuando un admin usa las acciones masivas. **NO se programan**.

### `alumnos.tasks.crear_usuario_teams_async`
**Categoría**: 🔘 Tarea bajo demanda

**Qué hace**:
- Crea cuenta de usuario en Microsoft Teams/Azure AD
- Genera email institucional: `aXXXXXXXX@eco.unrc.edu.ar`
- Asigna licencia y permisos básicos
- **NO envía email** (solo crea la cuenta)

**Cuándo se ejecuta**:
- Por acción: Admin → Alumnos → Seleccionar → "👤 Crear usuario en Teams (sin email)"

**¿Programar?**: ❌ NO

---

### `alumnos.tasks.activar_servicios_alumno`
**Categoría**: 🔘 Tarea bajo demanda

**Qué hace**:
- **Flujo completo de activación**:
  1. Crea usuario en Teams
  2. Enrolla en cursos Moodle
  3. Envía email con credenciales
- Es un **workflow orquestado** de varias tareas

**Cuándo se ejecuta**:
- Por acción: Admin → Alumnos → Seleccionar → "🚀 Activar Teams + Enviar Email"

**¿Programar?**: ❌ NO

**Requiere**:
- Alumno con email configurado
- Estado debe ser aspirante/ingresante

---

### `alumnos.tasks.enrollar_moodle_task`
**Categoría**: 🔘 Tarea bajo demanda

**Qué hace**:
- Enrolla alumno en cursos de Moodle según su modalidad
- Opcionalmente envía email de bienvenida
- Marca `moodle_procesado = True`

**Cuándo se ejecuta**:
- Por acción: Admin → Alumnos → Seleccionar → "🎓 Enrollar en Moodle"

**¿Programar?**: ❌ NO

**Parámetros**:
- `enviar_email=True/False`: Controla si envía email

---

### `alumnos.tasks.enviar_email_credenciales`
**Categoría**: 🔘 Tarea bajo demanda

**Qué hace**:
- Envía email con credenciales de acceso al alumno
- Incluye: email, contraseña temporal, links a servicios
- Usa plantillas HTML personalizadas

**Cuándo se ejecuta**:
- Por acción: Admin → Alumnos → Seleccionar → "📧 Enviar email de bienvenida"
- Automáticamente al final de `activar_servicios_alumno`

**¿Programar?**: ❌ NO

---

### `alumnos.tasks.resetear_password_y_enviar_email`
**Categoría**: 🔘 Tarea bajo demanda

**Qué hace**:
- Genera nueva contraseña temporal en Teams/Azure AD
- Envía email con la nueva contraseña
- Marca contraseña como "debe cambiar en próximo login"

**Cuándo se ejecuta**:
- Por acción: Admin → Alumnos → Seleccionar → "🔄 Generar contraseña y enviar correo"

**¿Programar?**: ❌ NO

---

## 🗑️ TAREAS DE ELIMINACIÓN

**⚠️ PELIGRO**: Estas tareas eliminan datos de forma **irreversible**.

### `alumnos.tasks_delete.eliminar_solo_teams`
**Categoría**: 🔘⚠️ Tarea bajo demanda (PELIGROSA)

**Qué hace**:
- Elimina cuenta de Microsoft Teams/Azure AD
- **NO toca Moodle** (el alumno sigue en Moodle)
- Marca `teams_procesado = False`

**Cuándo se ejecuta**:
- Por acción: Admin → Alumnos → Seleccionar → "🗑️ Borrar solo de Teams"

**¿Programar?**: ❌ NO (es acción crítica)

---

### `alumnos.tasks_delete.eliminar_solo_moodle`
**Categoría**: 🔘⚠️ Tarea bajo demanda (PELIGROSA)

**Qué hace**:
- Elimina enrollamientos de Moodle
- **NO toca Teams** (la cuenta Teams sigue activa)
- Marca `moodle_procesado = False`

**Cuándo se ejecuta**:
- Por acción: Admin → Alumnos → Seleccionar → "🗑️ Borrar solo de Moodle"

**¿Programar?**: ❌ NO

---

### `alumnos.tasks_delete.eliminar_alumno_completo`
**Categoría**: 🔘⚠️ Tarea bajo demanda (MUY PELIGROSA)

**Qué hace**:
- **Eliminación completa en 3 pasos**:
  1. Elimina de Teams/Azure AD
  2. Elimina de Moodle
  3. Elimina de base de datos PyLucy
- **IRREVERSIBLE**: No hay rollback

**Cuándo se ejecuta**:
- Por acción: Admin → Alumnos → Seleccionar → "🗑️💀 Eliminar alumno completamente"

**¿Programar?**: ❌❌❌ NUNCA

**⚠️ Úsala solo para**:
- Alumnos de prueba
- Datos duplicados
- Limpieza de testing

---

### `alumnos.tasks.eliminar_cuenta_externa`
**Categoría**: 🔘⚠️ Tarea bajo demanda (PELIGROSA)

**Qué hace**:
- Similar a `eliminar_alumno_completo` pero:
- Solo elimina de sistemas externos (Teams + Moodle)
- **NO elimina de la BD** (el registro queda)

**Cuándo se ejecuta**:
- Por acción del admin (si está configurada)

**¿Programar?**: ❌ NO

---

## 🔄 TAREAS DE PROCESAMIENTO POR LOTES

### `alumnos.tasks.procesar_lote_alumnos_nuevos`
**Categoría**: ⏰ Tarea programable (OPCIONAL)

**Qué hace**:
- Procesa múltiples alumnos nuevos en un lote
- Aplica rate limiting manual
- Útil para procesar grandes volúmenes

**Cuándo usarla**:
- Para procesar lotes de alumnos en horarios específicos
- Para ejecutar fuera del horario de oficina
- Para evitar saturar APIs en horario pico

**¿Programar?**: ✅ SÍ (opcional, según necesidad)

**Ejemplo de programación**:
```
Name: Procesamiento Nocturno de Nuevos Alumnos
Task: alumnos.tasks.procesar_lote_alumnos_nuevos
Crontab: 0 2 * * * (Diario a las 2 AM)
Enabled: True
```

---

### `alumnos.tasks.procesar_alumno_nuevo_completo`
**Categoría**: 🔘 Tarea bajo demanda

**Qué hace**:
- Workflow completo para un alumno individual
- Detecta estado y aplica acciones correspondientes
- Orquesta: Teams → Moodle → Email

**Cuándo se ejecuta**:
- Por trigger interno al crear alumno
- Por acción manual

**¿Programar?**: ❌ NO

---

## 🧪 TAREAS DE DEBUG Y EJEMPLO

### `pylucy.celery.debug_task`
**Categoría**: 🧪 Debug

**Qué hace**:
- Tarea mínima para verificar que Celery funciona
- Imprime información del request
- No hace nada útil

**Cuándo usarla**:
- Para verificar que Celery está corriendo
- Para debug de configuración

**¿Programar?**: ❌ NO (solo para testing)

---

### `alumnos.tasks.tarea_personalizada_ejemplo`
**Categoría**: 🧪 Ejemplo

**Qué hace**:
- Tarea de ejemplo para aprender a crear personalizadas
- Cuenta alumnos activos y loguea
- Retorna resultado de ejemplo

**Cuándo usarla**:
- Como plantilla para crear tus propias tareas
- Para aprender la estructura

**¿Programar?**: ✅ SÍ (solo si quieres probar)

**Ejemplo**:
```
Name: Prueba de Tarea Personalizada
Task: alumnos.tasks.tarea_personalizada_ejemplo
Crontab: */10 * * * * (Cada 10 minutos)
Enabled: True
Description: Tarea de prueba que cuenta alumnos activos
```

---

## 📋 RESUMEN: ¿Cuáles Programar?

### ✅ YA PROGRAMADAS (No tocar)
- ✅ `procesar_cola_tareas_pendientes` → Cada 5 min
- ✅ `ingestar_preinscriptos` → Cada 5 min
- ✅ `ingestar_aspirantes` → Cada 5 min
- ✅ `ingestar_ingresantes` → Cada 5 min
- ✅ `celery.backend_cleanup` → Diario 4 AM

### ⏰ OPCIONALES (Programar según necesidad)
- `procesar_lote_alumnos_nuevos` → Para procesamiento nocturno
- Tus tareas personalizadas

### ❌ NUNCA PROGRAMAR (Solo bajo demanda)
- `crear_usuario_teams_async`
- `activar_servicios_alumno`
- `enrollar_moodle_task`
- `enviar_email_credenciales`
- `resetear_password_y_enviar_email`
- `eliminar_solo_teams`
- `eliminar_solo_moodle`
- `eliminar_alumno_completo`
- `ingesta_manual_task`

---

## 🔍 Cómo Saber Qué Hace una Tarea

### Opción 1: Ver código fuente
```bash
# Abrir tasks.py
nano /home/carlos/work/pylucy/src/alumnos/tasks.py

# Buscar la función
# Ej: def ingestar_preinscriptos(self):
```

### Opción 2: Ver docstring
```python
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.tasks import ingestar_preinscriptos
print(ingestar_preinscriptos.__doc__)
"
```

### Opción 3: Ver logs de ejecuciones pasadas
```bash
# Ver logs de celery
docker compose -f docker-compose.testing.yml logs celery | grep "nombre_tarea"

# Ver tabla de Tareas Asíncronas en Admin
# Admin → Tareas Asíncronas → Filtrar por tipo
```

---

## 📖 Documentos Relacionados

- `ARQUITECTURA_COLAS.md` - Cómo funciona el sistema de colas
- `GUIA_TAREAS_PERSONALIZADAS.md` - Cómo crear tus propias tareas
- `PRUEBAS_SISTEMA_COLAS.md` - Cómo probar el sistema

---

## 📊 RESUMEN EJECUTIVO

### Tabla Completa de Tareas Disponibles

| # | Nombre Tarea | Función | Ya Programada | Para Qué |
|---|--------------|---------|---------------|----------|
| 1 | `procesar_cola_tareas_pendientes` | Procesador de cola con rate limiting | ✅ Cada 5 min | Sistema de colas interno |
| 2 | `ingestar_preinscriptos` | Sincronizar preinscriptos (incremental) | ✅ Cada 5 min | Ingesta automática |
| 3 | `ingestar_aspirantes` | Sincronizar aspirantes (incremental) | ✅ Cada 5 min | Ingesta automática |
| 4 | `ingestar_ingresantes` | Sincronizar ingresantes (incremental) | ✅ Cada 5 min | Ingesta automática |
| 5 | `celery.backend_cleanup` | Limpiar resultados viejos en Redis | ✅ Diario 4 AM | Mantenimiento |
| 6 | `ingesta_manual_task` | Ingesta manual desde Admin → Alumnos | ❌ Manual | Botón "Consumir" con desde/hasta |
| 7 | `crear_usuario_teams_async` | Crear cuenta Teams sin email | ❌ Acción admin | Activación manual |
| 8 | `activar_servicios_alumno` | Teams + Moodle + Email completo | ❌ Acción admin | Activación full |
| 9 | `enrollar_moodle_task` | Enrollar en cursos Moodle | ❌ Acción admin | Matriculación |
| 10 | `enviar_email_credenciales` | Enviar email con credenciales | ❌ Acción admin | Notificación |
| 11 | `resetear_password_y_enviar_email` | Resetear contraseña + email | ❌ Acción admin | Recuperación |
| 12 | `eliminar_solo_teams` | Borrar cuenta Teams únicamente | ❌ Acción admin | Baja parcial ⚠️ |
| 13 | `eliminar_solo_moodle` | Borrar enrollamiento Moodle únicamente | ❌ Acción admin | Baja parcial ⚠️ |
| 14 | `eliminar_alumno_completo` | Teams + Moodle + BD completo | ❌ Acción admin | Baja total ⚠️⚠️ |
| 15 | `eliminar_cuenta_externa` | Teams + Moodle (no BD) | ❌ Acción admin | Baja externa ⚠️ |
| 16 | `procesar_lote_alumnos_nuevos` | Procesar lote con rate limiting | ⏰ Opcional | Procesamiento nocturno |
| 17 | `procesar_alumno_nuevo_completo` | Workflow individual completo | ❌ Trigger | Orquestación |
| 18 | `tarea_personalizada_ejemplo` | Ejemplo de tarea custom | 🧪 Prueba | Aprendizaje/plantilla |
| 19 | `debug_task` | Verificar Celery funciona | 🧪 Debug | Testing Celery |

### Leyenda Rápida

| Símbolo | Significado |
|---------|-------------|
| ✅ | Ya programada automáticamente - NO tocar |
| ❌ | NO programar - Solo uso manual/acción admin |
| ⏰ | Programable según necesidad |
| 🧪 | Testing/ejemplo |
| ⚠️ | Peligrosa - Eliminación irreversible |

---

**Última actualización**: 2025-12-27 (Consulta incremental - ingesta manual en Admin → Alumnos)
