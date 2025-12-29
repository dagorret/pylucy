# Flujo Automático de Ingesta y Procesamiento

## 1️⃣ Celery Beat (cada 5 minutos)

```
┌─────────────────────────────────────────────────────────────┐
│  CELERY BEAT (Programador)                                  │
│  Crontab: */5 * * * * (cada 5 minutos)                      │
└─────────────────────────────────────────────────────────────┘
           │
           ├──► ingestar_preinscriptos()
           ├──► ingestar_aspirantes()
           ├──► ingestar_ingresantes()
           └──► procesar_cola_tareas_pendientes()
```

---

## 2️⃣ Tareas de Ingesta (verifican horario antes de ejecutar)

### ingestar_preinscriptos()
```
┌─────────────────────────────────────────────────────────────┐
│ 1. Verificar si está habilitada (dia_inicio existe)         │
│ 2. Verificar si está en rango de fechas                     │
│    - Si ahora < dia_inicio → SALIR                          │
│    - Si ahora > dia_fin → SALIR                             │
│ 3. Calcular desde/hasta para consulta incremental           │
│    - Si forzar_carga_completa = True → desde dia_inicio     │
│    - Si ultima_ingesta existe → desde ultima_ingesta + 1s   │
│    - Si no → carga completa                                 │
│ 4. Llamar a API UTI/SIAL con rate_limit_uti                │
│ 5. Por cada alumno nuevo detectado:                         │
│    ┌─────────────────────────────────────────────────────┐  │
│    │ PREINSCRIPTOS → Solo email bienvenida (si config)   │  │
│    │ NO se crea Teams ni Moodle                           │  │
│    └─────────────────────────────────────────────────────┘  │
│ 6. Actualizar ultima_ingesta_preinscriptos = ahora          │
│ 7. Log: "Ingesta" si creados+actualizados > 0               │
│         "Chequeo de Ingesta" si creados+actualizados = 0    │
└─────────────────────────────────────────────────────────────┘
```

### ingestar_aspirantes()
```
┌─────────────────────────────────────────────────────────────┐
│ 1-4. Igual que preinscriptos                                 │
│ 5. Por cada alumno nuevo detectado:                         │
│    ┌─────────────────────────────────────────────────────┐  │
│    │ ASPIRANTES → Si config activado:                     │  │
│    │   ✅ Email de bienvenida                             │  │
│    │   ✅ Tarea CREAR_USUARIO_TEAMS (→ cola)              │  │
│    │   ✅ Tarea MOODLE_ENROLL (→ cola)                    │  │
│    └─────────────────────────────────────────────────────┘  │
│ 6. Actualizar ultima_ingesta_aspirantes = ahora             │
└─────────────────────────────────────────────────────────────┘
```

### ingestar_ingresantes()
```
┌─────────────────────────────────────────────────────────────┐
│ Igual que aspirantes pero con:                              │
│ - ultima_ingesta_ingresantes                                 │
│ - ingresantes_dia_inicio/fin                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 3️⃣ Procesamiento de Cola (respeta rate limits)

### procesar_cola_tareas_pendientes()
```
┌─────────────────────────────────────────────────────────────┐
│ 1. Buscar tareas con estado=PENDING (ordenadas por fecha)   │
│ 2. Tomar hasta batch_size tareas                            │
│ 3. Agrupar por tipo de tarea                                │
│ 4. Por cada tipo:                                           │
│    ┌─────────────────────────────────────────────────────┐  │
│    │ procesar_lote_por_tipo_tarea()                       │  │
│    │   - Determinar rate_limit según tipo:               │  │
│    │     • CREAR_USUARIO_TEAMS → rate_limit_teams        │  │
│    │     • RESETEAR_PASSWORD → rate_limit_teams          │  │
│    │     • ENVIAR_EMAIL → rate_limit_teams               │  │
│    │     • MOODLE_ENROLL → rate_limit_moodle             │  │
│    │     • INGESTA_* → rate_limit_uti                    │  │
│    │   - Calcular delay = 60 / rate_limit                │  │
│    │   - Por cada tarea:                                  │  │
│    │       1. Marcar RUNNING                              │  │
│    │       2. ejecutar_tarea_segun_tipo()                 │  │
│    │       3. Marcar COMPLETED o FAILED                   │  │
│    │       4. time.sleep(delay) ← RATE LIMITING           │  │
│    └─────────────────────────────────────────────────────┘  │
│ 5. Log resumen: X exitosas, Y fallidas                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 4️⃣ Ejecución de Tareas Específicas

### ejecutar_crear_usuario_teams(tarea)
```
┌─────────────────────────────────────────────────────────────┐
│ 1. Obtener alumno_id desde tarea                            │
│ 2. Crear usuario en Teams (TeamsService.crear_usuario)      │
│ 3. Si detalles['enviar_email'] = True:                      │
│    ┌─────────────────────────────────────────────────────┐  │
│    │ EmailService.send_credentials_email()                │  │
│    │ - Plantilla HTML con diseño FCE                      │  │
│    │ - Envía a email_personal del alumno                  │  │
│    │ - UPN + password temporal                            │  │
│    └─────────────────────────────────────────────────────┘  │
│ 4. Retornar {success: True/False, detalles: {...}}          │
└─────────────────────────────────────────────────────────────┘
```

### ejecutar_enrollar_moodle(tarea)
```
┌─────────────────────────────────────────────────────────────┐
│ 1. Obtener alumno_id desde tarea                            │
│ 2. Resolver cursos según carreras_data del alumno           │
│ 3. Enrollar en Moodle (MoodleService)                       │
│ 4. Si detalles['enviar_email'] = True:                      │
│    ┌─────────────────────────────────────────────────────┐  │
│    │ EmailService.send_enrollment_email()                 │  │
│    │ - Plantilla HTML con diseño FCE                      │  │
│    │ - Lista de cursos enrollados                         │  │
│    │ - Acceso a v.eco.unrc.edu.ar                         │  │
│    └─────────────────────────────────────────────────────┘  │
│ 5. Retornar {success: True/False, detalles: {...}}          │
└─────────────────────────────────────────────────────────────┘
```

---

## 5️⃣ Resumen del Flujo Completo

### Ejemplo: Aspirante Nuevo Detectado

```
TIEMPO | ACCIÓN
───────┼──────────────────────────────────────────────────────
00:00  │ Beat ejecuta ingestar_aspirantes()
00:00  │   └─► API UTI/SIAL detecta 1 aspirante nuevo
00:00  │   └─► Crear registro Alumno en BD
00:00  │   └─► EmailService.send_welcome_email() ← INMEDIATO
00:00  │   └─► Crear Tarea(tipo=CREAR_USUARIO_TEAMS, estado=PENDING)
00:00  │   └─► Crear Tarea(tipo=MOODLE_ENROLL, estado=PENDING)
───────┼──────────────────────────────────────────────────────
00:05  │ Beat ejecuta procesar_cola_tareas_pendientes()
00:05  │   └─► Procesar CREAR_USUARIO_TEAMS
00:05  │       └─► TeamsService.crear_usuario()
00:05  │       └─► EmailService.send_credentials_email() ← AQUÍ
00:05  │       └─► Marcar tarea COMPLETED
00:05  │       └─► time.sleep(60/rate_limit_teams)
00:05  │   └─► Procesar MOODLE_ENROLL
00:05  │       └─► MoodleService.enroll()
00:05  │       └─► EmailService.send_enrollment_email() ← AQUÍ
00:05  │       └─► Marcar tarea COMPLETED
───────┼──────────────────────────────────────────────────────
TOTAL  │ Aspirante recibe 3 emails:
       │   1. Bienvenida (inmediato)
       │   2. Credenciales Teams (max 5 min después)
       │   3. Enrollamiento Moodle (max 5 min después)
```

---

## 6️⃣ Configuración Clave

### En Admin → Configuración
```python
# Rate Limits (tareas por minuto)
rate_limit_teams = 10   # Graph API Teams
rate_limit_moodle = 20  # Moodle Web Services
rate_limit_uti = 5      # API UTI/SIAL

# Batch Size
batch_size = 50         # Tareas a procesar por ejecución

# Flags de envío (por categoría)
preinscriptos_enviar_email = True   # Solo bienvenida
aspirantes_activar_teams = True     # Crear Teams + email
aspirantes_activar_moodle = True    # Enrollar + email
```

### En Celery Beat (Admin → Periodic Tasks)
```python
# Todas con crontab: */5 * * * *
- Procesador de Cola de Tareas (enabled=True)
- Ingesta Automática de Preinscriptos (enabled=True)
- Ingesta Automática de Aspirantes (enabled=True)
- Ingesta Automática de Ingresantes (enabled=True)
```

---

**Autor**: Carlos Dagorret  
**Fecha**: 2025-12-29  
**Licencia**: MIT
