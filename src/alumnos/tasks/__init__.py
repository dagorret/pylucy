"""
Nombre del Módulo: __init__.py

Descripción:
Exporta todas las tareas de Celery para mantener compatibilidad con imports existentes.

Autor: Carlos Dagorret
Fecha de Creación: 2025-12-29
Última Modificación: 2025-12-29

Licencia: MIT
Copyright (c) 2025 Carlos Dagorret

Uso:
    # Imports antiguos siguen funcionando:
    from alumnos.tasks import ingestar_preinscriptos
    from alumnos.tasks import crear_usuario_teams_async

    # También se puede importar desde submódulos:
    from alumnos.tasks.ingesta import ingestar_preinscriptos
    from alumnos.tasks.teams import crear_usuario_teams_async
"""

# Tareas de ingesta desde SIAL
from .ingesta import (
    ingestar_preinscriptos,
    ingestar_aspirantes,
    ingestar_ingresantes,
    ingesta_manual_task,
)

# Tareas de Microsoft Teams
from .teams import (
    crear_usuario_teams_async,
    resetear_password_y_enviar_email,
    eliminar_cuenta_externa,
    enviar_email_credenciales,
)

# Tareas de Moodle
from .moodle import (
    enrollar_moodle_task,
)

# Tareas de procesamiento de cola
from .procesamiento import (
    procesar_cola_tareas_pendientes,
    procesar_lote_por_tipo_tarea,
    ejecutar_tarea_segun_tipo,
    ejecutar_crear_usuario_teams,
    ejecutar_resetear_password,
    ejecutar_enrollar_moodle,
    ejecutar_activar_servicios,
    ejecutar_eliminar_cuenta,
    ejecutar_enviar_email,
)

# Funciones auxiliares
from .helpers import (
    activar_servicios_alumno,
    procesar_alumno_nuevo_completo,
    procesar_lote_alumnos_nuevos,
)

# Tareas personalizadas
from .personalizadas import (
    tarea_personalizada_ejemplo,
    ejecutar_tarea_personalizada,
)

# Exportar todas las tareas públicas
__all__ = [
    # Ingesta
    'ingestar_preinscriptos',
    'ingestar_aspirantes',
    'ingestar_ingresantes',
    'ingesta_manual_task',

    # Teams
    'crear_usuario_teams_async',
    'resetear_password_y_enviar_email',
    'eliminar_cuenta_externa',
    'enviar_email_credenciales',

    # Moodle
    'enrollar_moodle_task',

    # Procesamiento
    'procesar_cola_tareas_pendientes',
    'procesar_lote_por_tipo_tarea',
    'ejecutar_tarea_segun_tipo',
    'ejecutar_crear_usuario_teams',
    'ejecutar_resetear_password',
    'ejecutar_enrollar_moodle',
    'ejecutar_activar_servicios',
    'ejecutar_eliminar_cuenta',
    'ejecutar_enviar_email',

    # Helpers
    'activar_servicios_alumno',
    'procesar_alumno_nuevo_completo',
    'procesar_lote_alumnos_nuevos',

    # Personalizadas
    'tarea_personalizada_ejemplo',
    'ejecutar_tarea_personalizada',
]
