# Sistema de Tareas Asíncronas y Periódicas - Lucy AMS

## ¿Para qué sirve?

El sistema de tareas permite ejecutar operaciones en segundo plano (background) sin bloquear el navegador:

1. **Tareas Asíncronas**: Se ejecutan cuando el usuario realiza una acción (crear usuario, enviar email, eliminar)
2. **Tareas Periódicas**: Se ejecutan automáticamente según un horario configurado (ingesta diaria, limpieza semanal)

## Tareas Registradas en el Sistema

### 1. Tareas de Ingesta Automática (Periódicas)

Estas tareas deben configurarse en **django-celery-beat** para que se ejecuten automáticamente.

#### `alumnos.tasks.ingestar_preinscriptos`

- **Descripción**: Ingesta automática de preinscriptos desde SIAL
- **Cuándo se ejecuta**: Según configuración en tabla Configuración
- **Validación**:
  - Solo se ejecuta si `preinscriptos_dia_inicio` está configurado
  - Solo si la fecha/hora actual está entre `dia_inicio` y `dia_fin`
- **Resultado**: Crea/actualiza alumnos con estado "preinscripto"
- **Tabla Tarea**: Registra cantidad de creados/actualizados

#### `alumnos.tasks.ingestar_aspirantes`

- **Descripción**: Ingesta automática de aspirantes desde SIAL
- **Cuándo se ejecuta**: Según configuración en tabla Configuración
- **Validación**: Similar a preinscriptos
- **Resultado**: Crea/actualiza alumnos con estado "aspirante"

#### `alumnos.tasks.ingestar_ingresantes`

- **Descripción**: Ingesta automática de ingresantes desde SIAL
- **Cuándo se ejecuta**: Según configuración en tabla Configuración
- **Validación**: Similar a preinscriptos
- **Resultado**: Crea/actualiza alumnos con estado "ingresante"

**IMPORTANTE**: Estas tareas verifican automáticamente las fechas configuradas en `/admin/alumnos/configuracion/`. Si las fechas no están configuradas o no estamos en el rango, la tarea no hace nada.

### 2. Tareas de Gestión de Usuarios (Asíncronas)

Estas se ejecutan automáticamente cuando realizas acciones desde el admin.

#### `alumnos.tasks.activar_servicios_alumno`

- **Descripción**: Crea usuario en Teams y envía email con credenciales
- **Se ejecuta**: Cuando usas la acción "🚀 Activar Teams + Enviar Email"
- **Parámetros**: `alumno_id`
- **Resultado**: Usuario creado + email enviado
- **Tabla Tarea**: Muestra si fue exitoso o falló

#### `alumnos.tasks.crear_usuario_teams_async`

- **Descripción**: Solo crea usuario en Teams (sin enviar email)
- **Se ejecuta**: Cuando usas la acción "👤 Crear usuario en Teams (sin email)"
- **Parámetros**: `alumno_id`
- **Resultado**: Usuario creado, contraseña en campo `detalles` de la tarea
- **Tabla Tarea**: Muestra UPN y password en detalles JSON

#### `alumnos.tasks.resetear_password_y_enviar_email`

- **Descripción**: Resetea contraseña de usuario existente y envía email
- **Se ejecuta**: Cuando usas la acción "🔄 Generar contraseña y enviar correo"
- **Parámetros**: `alumno_id`
- **Resultado**: Password reseteado + email enviado
- **Tabla Tarea**: Muestra resultado del reseteo

### 3. Tareas de Comunicación (Asíncronas)

#### `alumnos.tasks.enviar_email_credenciales`

- **Descripción**: Envía email con credenciales de acceso
- **Se ejecuta**: Llamada por otras tareas que necesitan enviar email
- **Parámetros**: `alumno_id`, `teams_data` (diccionario con upn/password)
- **Resultado**: Email enviado
- **Tabla Tarea**: Muestra si el email se envió correctamente

### 4. Tareas de Eliminación (Asíncronas)

#### `alumnos.tasks.eliminar_cuenta_externa`

- **Descripción**: Elimina cuenta de Teams y Moodle de un alumno
- **Se ejecuta**: Automáticamente cuando eliminas un alumno desde el admin
- **Parámetros**: `alumno_id`, `upn`
- **Seguridad**: Solo elimina cuentas con prefijo `test-`
- **Resultado**: Cuenta eliminada de sistemas externos
- **Tabla Tarea**: Registra la eliminación

## Configurar Tareas Periódicas

### Acceso

Ir a: **http://localhost:8000/admin/django_celery_beat/periodictask/**

### Campos del Formulario

#### **Name** (Nombre)

- **Descripción**: Nombre descriptivo de la tarea
- **Ejemplo**: `Ingesta diaria de preinscriptos`
- **Recomendación**: Usar nombres claros en español

#### **Task (registered)** (Tarea registrada)

- **Descripción**: Nombre técnico de la tarea a ejecutar
- **Opciones disponibles**:
  - `alumnos.tasks.ingestar_preinscriptos`
  - `alumnos.tasks.ingestar_aspirantes`
  - `alumnos.tasks.ingestar_ingresantes`
- **Ejemplo**: `alumnos.tasks.ingestar_preinscriptos`

#### **Enabled** (Habilitada)

- **Descripción**: Si la tarea está activa o no
- **Opciones**: ✓ Sí / ☐ No
- **Uso**: Desmarca para pausar temporalmente una tarea sin borrarla

#### **Interval** (Intervalo)

- **Descripción**: Cada cuánto tiempo se ejecuta la tarea
- **Uso**: Debes crear primero un "Interval schedule"
- **Ejemplo**: "Cada 1 hora", "Cada 30 minutos", "Cada 1 día"

#### **Crontab** (Programación tipo cron)

- **Descripción**: Horario específico (estilo cron de Linux)
- **Uso**: Más preciso que Interval
- **Ejemplo**: "Todos los días a las 2:00 AM"

#### **Solar**

- **Descripción**: Basado en eventos solares (amanecer/atardecer)
- **Uso**: Raramente usado
- **Recomendación**: Ignorar para este proyecto

#### **Clocked**

- **Descripción**: Ejecutar una sola vez en fecha/hora específica
- **Uso**: Para tareas que se ejecutan una única vez
- **Ejemplo**: "15 de Enero 2026 a las 10:00"

#### **Start datetime** (Fecha/hora de inicio)

- **Descripción**: Cuándo empezar a ejecutar esta tarea periódica
- **Opcional**: Si está vacío, empieza inmediatamente
- **Ejemplo**: `2026-01-01 00:00:00`

#### **Expires** (Fecha de expiración)

- **Descripción**: Cuándo dejar de ejecutar esta tarea
- **Opcional**: Si está vacío, se ejecuta indefinidamente
- **Ejemplo**: `2026-01-31 23:59:59`

#### **One-off task** (Tarea de una sola vez)

- **Descripción**: Ejecutar solo una vez y deshabilitarse automáticamente
- **Uso**: Para tareas puntuales
- **Ejemplo**: Marcar si solo quieres que se ejecute una vez

## Ejemplos de Configuración

### Ejemplo 1: Ingesta de Preinscriptos cada 1 hora

```
✓ Paso 1: Crear Interval Schedule
- Ir a: /admin/django_celery_beat/intervalschedule/
- Every: 1
- Period: Hours
- Guardar

✓ Paso 2: Crear Periodic Task
- Name: "Ingesta horaria de preinscriptos"
- Task: alumnos.tasks.ingestar_preinscriptos
- Enabled: ✓
- Interval: [Seleccionar "every 1 hour"]
- Start datetime: (vacío o fecha deseada)
- Guardar

✓ Paso 3: Configurar rango de fechas en Configuración
- Ir a: /admin/alumnos/configuracion/
- Preinscriptos día inicio: 2026-01-01 00:00:00
- Preinscriptos día fin: 2026-01-15 23:59:59
- Guardar
```

**Resultado**: La tarea se ejecutará cada hora, pero solo ingresará datos si estamos entre el 1 y 15 de Enero 2026.

### Ejemplo 2: Ingesta de Aspirantes cada día a las 2:00 AM

```
✓ Paso 1: Crear Crontab Schedule
- Ir a: /admin/django_celery_beat/crontabschedule/
- Minute: 0
- Hour: 2
- Day of week: * (todos)
- Day of month: * (todos)
- Month of year: * (todos)
- Timezone: America/Argentina/Cordoba
- Guardar

✓ Paso 2: Crear Periodic Task
- Name: "Ingesta diaria de aspirantes (2 AM)"
- Task: alumnos.tasks.ingestar_aspirantes
- Enabled: ✓
- Crontab: [Seleccionar "0 2 * * * (m/h/dM/MY/d)"]
- Guardar

✓ Paso 3: Configurar en Configuración
- Aspirantes día inicio: 2026-02-01 00:00:00
- Aspirantes día fin: 2026-02-28 23:59:59
- Guardar
```

**Resultado**: Cada día a las 2:00 AM, si estamos en Febrero 2026, ingresará aspirantes.

### Ejemplo 3: Ingesta de Ingresantes cada 30 minutos (solo días laborables)

```
✓ Paso 1: Crear Crontab Schedule
- Minute: */30 (cada 30 minutos)
- Hour: * (todas las horas)
- Day of week: 1-5 (lunes a viernes)
- Day of month: *
- Month of year: *
- Timezone: America/Argentina/Cordoba
- Guardar

✓ Paso 2: Crear Periodic Task
- Name: "Ingesta de ingresantes (L-V cada 30 min)"
- Task: alumnos.tasks.ingestar_ingresantes
- Enabled: ✓
- Crontab: [Seleccionar el crontab creado]
- Guardar

✓ Paso 3: Configurar en Configuración
- Ingresantes día inicio: 2026-03-01 00:00:00
- Ingresantes día fin: 2026-03-31 23:59:59
- Guardar
```

**Resultado**: Cada 30 minutos de Lunes a Viernes, si estamos en Marzo 2026, ingresará ingresantes.

## Cómo Funciona el Sistema

### Flujo de Tareas Periódicas

```
┌─────────────────────────────────────────┐
│ Celery Beat Scheduler                   │
│ (lee django_celery_beat_periodictask)   │
└───────────────┬─────────────────────────┘
                │
                │ Cuando llega la hora configurada
                ↓
┌─────────────────────────────────────────┐
│ Se ejecuta la tarea                     │
│ Ejemplo: ingestar_preinscriptos()       │
└───────────────┬─────────────────────────┘
                │
                │ 1. Verifica Configuración
                ↓
┌─────────────────────────────────────────┐
│ ¿Día inicio configurado?                │
│ ¿Estamos en el rango de fechas?         │
└───────────────┬─────────────────────────┘
                │
        ┌───────┴───────┐
        │ SÍ            │ NO
        ↓               ↓
┌──────────────┐  ┌─────────────┐
│ 2. Crea      │  │ Termina sin │
│ registro en  │  │ hacer nada  │
│ tabla Tarea  │  └─────────────┘
│ (estado:     │
│ RUNNING)     │
└──────┬───────┘
       │
       │ 3. Ejecuta ingesta desde SIAL
       ↓
┌──────────────────────────────────────┐
│ ingerir_desde_sial(tipo='...')       │
│ - Llama API SIAL                     │
│ - Crea/actualiza alumnos en BD       │
└──────┬───────────────────────────────┘
       │
       │ 4. Actualiza registro en tabla Tarea
       ↓
┌──────────────────────────────────────┐
│ Tarea actualizada:                   │
│ - Estado: COMPLETED                  │
│ - Cantidad entidades: 150            │
│ - Detalles: {created: 50,            │
│             updated: 100,            │
│             errors: 0}               │
│ - Hora fin: 2026-01-15 10:05:23      │
└──────────────────────────────────────┘
```

### Flujo de Tareas Asíncronas (acción del admin)

```
Usuario en Admin
   │
   │ Selecciona alumnos y ejecuta acción
   │ "🚀 Activar Teams + Enviar Email"
   ↓
┌─────────────────────────────────────┐
│ Admin crea tarea en Celery          │
│ activar_servicios_alumno.delay()    │
└───────────┬─────────────────────────┘
            │
            │ Admin responde inmediatamente:
            │ "📋 5 tareas programadas"
            ↓
┌─────────────────────────────────────┐
│ Usuario ve el mensaje y puede       │
│ seguir trabajando en el admin       │
└─────────────────────────────────────┘

Mientras tanto, en background:
┌─────────────────────────────────────┐
│ Celery Worker procesa las 5 tareas  │
│ una por una                          │
└───────────┬─────────────────────────┘
            │
            │ Para cada alumno:
            ↓
┌─────────────────────────────────────┐
│ 1. Crea registro en tabla Tarea     │
│ 2. Crea usuario en Teams (API)      │
│ 3. Asigna licencia Microsoft 365    │
│ 4. Envía email con credenciales     │
│ 5. Actualiza registro (COMPLETED)   │
└─────────────────────────────────────┘

Usuario puede ver el progreso en:
/admin/alumnos/tarea/
o en el dashboard principal
```

## Monitoreo de Tareas

### Dashboard Principal

- **URL**: http://localhost:8000/admin/
- **Muestra**:
  - Últimas 10 tareas
  - Resumen: pendientes, ejecutando, completadas (24h), fallidas (24h)
  - Actualización: Recargar página

### Lista Completa de Tareas

- **URL**: http://localhost:8000/admin/alumnos/tarea/
- **Filtros**: Por tipo, estado, fecha
- **Búsqueda**: Por ID, alumno, usuario, error
- **Detalles**: Haz click en una tarea para ver JSON completo

### Logs del Sistema

- **URL**: http://localhost:8000/admin/alumnos/log/
- **Diferencia**:
  - **Tarea**: Tracking de ejecución (inicio/fin/duración)
  - **Log**: Eventos y errores detallados

## Troubleshooting

### La tarea periódica no se ejecuta

1. **Verificar que Celery Beat esté corriendo**:
   
   ```bash
   docker ps --filter "name=celery-beat"
   ```
   
   Debe mostrar "Up X minutes"

2. **Verificar que la tarea esté habilitada**:
   
   - Ir a `/admin/django_celery_beat/periodictask/`
   - Buscar tu tarea
   - Verificar que tenga ✓ en "Enabled"

3. **Verificar logs de Celery Beat**:
   
   ```bash
   docker logs pylucy-celery-beat-dev --tail 50
   ```

4. **Verificar configuración de fechas**:
   
   - Ir a `/admin/alumnos/configuracion/`
   - Verificar que `dia_inicio` y `dia_fin` estén configurados
   - Verificar que la fecha actual esté en el rango

### La tarea se ejecuta pero no hace nada

1. **Ver tabla de Tareas**:
   
   - Ir a `/admin/alumnos/tarea/`
   - Buscar la tarea más reciente
   - Ver el campo "Detalles" para entender qué pasó

2. **Revisar logs**:
   
   ```bash
   docker logs pylucy-celery-dev --tail 100 | grep "ingesta"
   ```

### La tarea falla (estado FAILED)

1. **Ver el mensaje de error**:
   
   - En `/admin/alumnos/tarea/`
   - Buscar la tarea fallida
   - Leer campo "Mensaje error"

2. **Errores comunes**:
   
   - **"Usuario ya existe"**: La cuenta ya fue creada previamente
   - **"Alumno X no encontrado"**: El alumno fue eliminado antes de que se procesara la tarea
   - **"Error 403"**: Problema de permisos en Azure AD
   - **"Error de conexión"**: SIAL no responde o está caído

## Mejores Prácticas

### Tareas Periódicas

1. **Horarios**: Ejecutar ingestas en horarios de baja carga (madrugada)
2. **Frecuencia**: No más de 1 vez cada 30 minutos para evitar sobrecarga
3. **Rangos de fechas**: Siempre configurar `dia_inicio` y `dia_fin` para evitar ejecuciones innecesarias
4. **Monitoreo**: Revisar tabla de Tareas semanalmente para detectar problemas

### Tareas Asíncronas

1. **Lotes pequeños**: Procesar máximo 50 alumnos por vez desde el admin
2. **Verificar antes**: Revisar que los alumnos tengan email antes de activar servicios
3. **No repetir**: Si ya activaste servicios para un alumno, no lo vuelvas a hacer
4. **Eliminar con cuidado**: Al eliminar alumnos, se eliminan automáticamente sus cuentas (irreversible en testing)

### Mantenimiento

1. **Limpiar tareas antiguas**: Eliminar tareas de más de 3 meses periódicamente
2. **Revisar fallidas**: Investigar por qué fallaron y corregir
3. **Backup**: La tabla de Tareas también se respalda con la BD

---

**Última actualización**: 2025-12-11
**Versión**: 1.0
