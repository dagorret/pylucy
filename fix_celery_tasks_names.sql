-- Fix: Actualizar nombres de tareas periódicas de Celery Beat
-- Las tareas se movieron a submódulos (tasks.ingesta, tasks.procesamiento)
-- Este script actualiza las referencias en django_celery_beat_periodictask

UPDATE django_celery_beat_periodictask
SET task = 'alumnos.tasks.ingesta.ingestar_aspirantes'
WHERE task = 'alumnos.tasks.ingestar_aspirantes';

UPDATE django_celery_beat_periodictask
SET task = 'alumnos.tasks.ingesta.ingestar_ingresantes'
WHERE task = 'alumnos.tasks.ingestar_ingresantes';

UPDATE django_celery_beat_periodictask
SET task = 'alumnos.tasks.ingesta.ingestar_preinscriptos'
WHERE task = 'alumnos.tasks.ingestar_preinscriptos';

UPDATE django_celery_beat_periodictask
SET task = 'alumnos.tasks.procesamiento.procesar_cola_tareas_pendientes'
WHERE task = 'alumnos.tasks.procesar_cola_tareas_pendientes';

-- Verificar resultado
SELECT id, name, task, enabled
FROM django_celery_beat_periodictask
WHERE enabled=true
ORDER BY id;
