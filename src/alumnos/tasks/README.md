# Módulo de Tareas - PyLucy

Este directorio contiene las tareas asíncronas de Celery organizadas en módulos especializados.

## Estructura

```
alumnos/tasks/
├── __init__.py           - Exporta todas las tareas (compatibilidad hacia atrás)
├── ingesta.py            - Tareas de ingesta automática desde SIAL
├── teams.py              - Tareas relacionadas con Microsoft Teams
├── moodle.py             - Tareas relacionadas con Moodle
├── procesamiento.py      - Procesamiento de cola de tareas pendientes
├── helpers.py            - Funciones auxiliares compartidas
└── personalizadas.py     - Tareas personalizadas del usuario
```

## Distribución de Funciones

### ingesta.py (758 líneas)
- `ingestar_preinscriptos` - Ingesta automática de preinscriptos desde SIAL
- `ingestar_aspirantes` - Ingesta automática de aspirantes desde SIAL
- `ingestar_ingresantes` - Ingesta automática de ingresantes desde SIAL
- `ingesta_manual_task` - Ingesta manual disparada desde el admin

### teams.py (371 líneas)
- `crear_usuario_teams_async` - Crear usuario en Microsoft Teams
- `resetear_password_y_enviar_email` - Resetear contraseña de Teams
- `eliminar_cuenta_externa` - Eliminar cuenta de Teams/Moodle
- `enviar_email_credenciales` - Enviar email con credenciales

### moodle.py (159 líneas)
- `enrollar_moodle_task` - Enrollar alumno en cursos de Moodle

### procesamiento.py (484 líneas)
- `procesar_cola_tareas_pendientes` - Procesador principal de la cola
- `procesar_lote_por_tipo_tarea` - Procesar lote con rate limiting
- `ejecutar_tarea_segun_tipo` - Dispatcher de tareas
- `ejecutar_crear_usuario_teams` - Ejecutor para crear usuarios Teams
- `ejecutar_resetear_password` - Ejecutor para resetear passwords
- `ejecutar_enrollar_moodle` - Ejecutor para enrollar en Moodle
- `ejecutar_activar_servicios` - Ejecutor para activar servicios
- `ejecutar_eliminar_cuenta` - Ejecutor para eliminar cuentas
- `ejecutar_enviar_email` - Ejecutor para enviar emails

### helpers.py (595 líneas)
- `activar_servicios_alumno` - Activar servicios según estado del alumno
- `procesar_alumno_nuevo_completo` - Workflow completo para alumno nuevo
- `procesar_lote_alumnos_nuevos` - Procesar lote de alumnos con rate limiting

### personalizadas.py (300 líneas)
- `tarea_personalizada_ejemplo` - Ejemplo de tarea personalizada
- `ejecutar_tarea_personalizada` - Ejecutor de tareas personalizadas
- `_ejecutar_ingesta_personalizada` - Ingesta SIAL personalizada
- `_ejecutar_accion_sobre_alumnos` - Acción sobre alumnos filtrados

## Compatibilidad

### Imports antiguos (siguen funcionando)
```python
from alumnos.tasks import ingestar_preinscriptos
from alumnos.tasks import crear_usuario_teams_async
from alumnos.tasks import enrollar_moodle_task
```

### Imports nuevos (también funcionan)
```python
from alumnos.tasks.ingesta import ingestar_preinscriptos
from alumnos.tasks.teams import crear_usuario_teams_async
from alumnos.tasks.moodle import enrollar_moodle_task
```

### Migraciones
Las migraciones que usan rutas como `alumnos.tasks.nombre_tarea` siguen funcionando correctamente.

## Estadísticas

- **Archivo original**: 2,623 líneas
- **Total nuevos módulos**: 2,774 líneas
- **Diferencia**: +151 líneas (headers MIT en cada módulo)

## Licencia

MIT License - Copyright (c) 2025 Carlos Dagorret

## Fecha de división

29 de diciembre de 2025
