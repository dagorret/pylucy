  📋 Explicación de Cada Tarea Disponible

  🔹 Tareas del Sistema de Colas y Procesamiento

  1. alumnos.tasks.procesar_cola_tareas_pendientes ⭐
    - Qué hace: Procesador principal del sistema de colas
    - Cuándo se ejecuta: Cada 5 minutos (ya configurada)
    - Para qué: Toma tareas PENDING de la BD y las ejecuta respetando batch_size y rate_limits
    - CRÍTICA: Esta es la tarea más importante del nuevo sistema
  2. alumnos.tasks.procesar_lote_alumnos_nuevos
    - Qué hace: Procesa un lote de alumnos nuevos
    - Cuándo: Bajo demanda o manual
    - Para qué: Procesar múltiples alumnos en batch

  ---
  🔹 Tareas de Ingesta Automática (API UTI/SIAL)

  3. alumnos.tasks.ingesta_preinscriptos ⭐
    - Qué hace: Ingesta automática de preinscriptos desde API UTI
    - Cuándo se ejecuta: Cada 5 minutos (ya configurada)
    - Para qué: Sincronizar datos de preinscripción
  4. alumnos.tasks.ingestar_aspirantes ⭐
    - Qué hace: Ingesta automática de aspirantes desde API UTI
    - Cuándo se ejecuta: Cada 5 minutos (ya configurada)
    - Para qué: Sincronizar datos de aspirantes
  5. alumnos.tasks.ingestar_ingresantes ⭐
    - Qué hace: Ingesta automática de ingresantes desde API UTI
    - Cuándo se ejecuta: Cada 5 minutos (ya configurada)
    - Para qué: Sincronizar datos de ingresantes
  6. alumnos.tasks.ingesta_manual_task
    - Qué hace: Ingesta manual (trigger por acción de admin)
    - Cuándo: Manual, no programada
    - Para qué: Ejecutar ingesta fuera del horario automático

  ---
  🔹 Tareas de Gestión de Alumnos (Teams/Moodle)

  7. alumnos.tasks.activar_servicios_alumno
    - Qué hace: Activa cuenta Teams + Moodle + envía email
    - Cuándo: Por acción atómica del admin
    - Para qué: Activación completa de servicios para un alumno
  8. alumnos.tasks.crear_usuario_teams_async
    - Qué hace: Crea usuario en Microsoft Teams
    - Cuándo: Por acción atómica del admin
    - Para qué: Crear cuenta Teams sin enviar email
  9. alumnos.tasks.enrollar_moodle_task
    - Qué hace: Enrolla alumno en cursos de Moodle
    - Cuándo: Por acción atómica del admin
    - Para qué: Matricular en Moodle con/sin email
  10. alumnos.tasks.enviar_email_credenciales
    - Qué hace: Envía email con credenciales de acceso
    - Cuándo: Por acción atómica del admin
    - Para qué: Notificar al alumno sus datos de acceso
  11. alumnos.tasks.resetear_password_y_enviar_email
    - Qué hace: Resetea contraseña en Teams y envía email
    - Cuándo: Por acción atómica del admin
    - Para qué: Recuperación de contraseña

  ---
  🔹 Tareas de Eliminación

  12. alumnos.tasks.eliminar_cuenta_externa
    - Qué hace: Elimina cuenta de sistemas externos (Teams/Moodle)
    - Cuándo: Por acción atómica del admin
    - Para qué: Dar de baja servicios externos
  13. alumnos.tasks_delete.eliminar_alumno_completo
    - Qué hace: Elimina alumno de Teams + Moodle + BD
    - Cuándo: Por acción atómica del admin
    - Para qué: Eliminación completa del sistema
    - ⚠️ PELIGROSA: Acción irreversible
  14. alumnos.tasks_delete.eliminar_solo_moodle
    - Qué hace: Elimina solo de Moodle (mantiene Teams)
    - Cuándo: Por acción atómica del admin
    - Para qué: Dar de baja solo en Moodle
  15. alumnos.tasks_delete.eliminar_solo_teams
    - Qué hace: Elimina solo de Teams (mantiene Moodle)
    - Cuándo: Por acción atómica del admin
    - Para qué: Dar de baja solo en Teams

  ---
  🔹 Tareas de Sistema

  16. pylucy.celery.debug_task
    - Qué hace: Tarea de debug/prueba de Celery
    - Cuándo: Manual o testing
    - Para qué: Verificar que Celery funciona

  ---
  ⭐ Tareas YA Configuradas (No agregar de nuevo)

  Estas 5 tareas ya están configuradas y funcionando:

  | Tarea                               | Schedule    | Estado   |
  |-------------------------------------|-------------|----------|
  | Procesador de Cola de Tareas        | */5 * * * * | ✅ Activa |
  | Ingesta Automática de Preinscriptos | */5 * * * * | ✅ Activa |
  | Ingesta Automática de Aspirantes    | */5 * * * * | ✅ Activa |
  | Ingesta Automática de Ingresantes   | */5 * * * * | ✅ Activa |
  | celery.backend_cleanup              | 0 4 * * *   | ✅ Activa |

  ---
  💡 Tareas Que Podrías Agregar Manualmente

  Si necesitas programar alguna tarea adicional, estas son útiles:

  - alumnos.tasks.procesar_lote_alumnos_nuevos - Para procesar lotes en horarios específicos
  - alumnos.tasks.ingesta_manual_task - Para ingestas programadas fuera del horario automático

  El resto son tareas "bajo demanda" que se ejecutan por acciones del admin, NO deberían programarse periódicamente.

