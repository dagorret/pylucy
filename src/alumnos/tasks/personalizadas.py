"""
Nombre del Módulo: personalizadas.py

Descripción:
Tareas personalizadas definidas por el usuario.

Autor: Carlos Dagorret
Fecha de Creación: 2025-12-29
Última Modificación: 2025-12-29

Licencia: MIT
Copyright (c) 2025 Carlos Dagorret
"""

import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from ..models import Tarea, Alumno
from ..services import ingerir_desde_sial

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def tarea_personalizada_ejemplo(self):
    """
    Tarea personalizada de ejemplo.

    Puedes crear tareas personalizadas para ejecutar cualquier código
    de forma programada (ej: domingos, diario, cada hora, etc).

    Uso:
    1. Crea tu tarea aquí siguiendo este patrón
    2. Reinicia celery: docker compose restart celery celery-beat
    3. En Admin → Tareas periódicas → Agregar
    4. Selecciona esta tarea del dropdown
    5. Asigna un crontab (horario)

    Ejemplo de uso:
    - Reportes semanales
    - Limpieza de datos
    - Backups programados
    - Notificaciones periódicas
    """
    logger.info("🎯 Ejecutando tarea personalizada de ejemplo")

    try:
        # Tu código personalizado aquí
        # Ejemplo: generar reporte, limpiar datos, enviar notificaciones, etc.

        # Ejemplo simple: contar alumnos activos
        from .models import Alumno
        total_activos = Alumno.objects.filter(activo=True).count()

        logger.info(f"📊 Total de alumnos activos: {total_activos}")

        return {
            'success': True,
            'mensaje': f'Tarea completada. Alumnos activos: {total_activos}',
            'timestamp': timezone.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error en tarea personalizada: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def ejecutar_tarea_personalizada(self, tarea_personalizada_id):
    """
    Ejecuta una tarea personalizada definida por el usuario.
    Esta tarea es llamada por Celery Beat según la periodicidad configurada.

    Args:
        tarea_personalizada_id: ID de la TareaPersonalizada a ejecutar
    """
    from .models import TareaPersonalizada, Tarea
    from django.utils import timezone

    try:
        tarea_config = TareaPersonalizada.objects.get(id=tarea_personalizada_id)
    except TareaPersonalizada.DoesNotExist:
        logger.error(f"TareaPersonalizada {tarea_personalizada_id} no existe")
        return {'success': False, 'error': 'Tarea no encontrada'}

    # Verificar si está activa
    if not tarea_config.activa:
        logger.info(f"[TareaPersonalizada] '{tarea_config.nombre}' está inactiva, omitiendo ejecución")
        return {'success': False, 'error': 'Tarea inactiva'}

    logger.info(f"[TareaPersonalizada] 🚀 Ejecutando '{tarea_config.nombre}'")
    logger.info(f"[TareaPersonalizada] Tipo: {tarea_config.get_tipo_usuario_display()}, Acción: {tarea_config.get_accion_display()}")

    inicio = timezone.now()

    try:
        # Actualizar contador de ejecuciones
        tarea_config.ultima_ejecucion = inicio
        tarea_config.cantidad_ejecuciones += 1
        tarea_config.save()

        # Ejecutar según el tipo de acción
        if tarea_config.accion == TareaPersonalizada.AccionTarea.INGESTA_SIAL:
            resultado = _ejecutar_ingesta_personalizada(tarea_config, self.request.id)

        elif tarea_config.accion in [
            TareaPersonalizada.AccionTarea.CREAR_USUARIO_TEAMS,
            TareaPersonalizada.AccionTarea.ENVIAR_EMAIL,
            TareaPersonalizada.AccionTarea.ACTIVAR_SERVICIOS,
            TareaPersonalizada.AccionTarea.MOODLE_ENROLL,
            TareaPersonalizada.AccionTarea.RESETEAR_PASSWORD
        ]:
            resultado = _ejecutar_accion_sobre_alumnos(tarea_config, self.request.id)

        else:
            resultado = {'success': False, 'error': f'Acción no implementada: {tarea_config.accion}'}

        duracion = (timezone.now() - inicio).total_seconds()
        logger.info(f"[TareaPersonalizada] ✅ '{tarea_config.nombre}' completada en {duracion:.2f}s")

        return resultado

    except Exception as e:
        logger.error(f"[TareaPersonalizada] ❌ Error ejecutando '{tarea_config.nombre}': {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {'success': False, 'error': str(e)}


def _ejecutar_ingesta_personalizada(tarea_config, celery_task_id):
    """
    Ejecuta una ingesta SIAL según configuración de TareaPersonalizada.
    """
    from .services import ingerir_desde_sial
    from .models import Tarea
    from datetime import timedelta

    # Mapear tipo de usuario a tipo de ingesta
    tipo_map = {
        'preinscripto': 'preinscriptos',
        'aspirante': 'aspirantes',
        'ingresante': 'ingresantes',
    }

    tipo_ingesta = tipo_map.get(tarea_config.tipo_usuario)
    if not tipo_ingesta:
        return {'success': False, 'error': f'Tipo de usuario no válido para ingesta: {tarea_config.tipo_usuario}'}

    # ✨ INGESTA INCREMENTAL: Usar ultima_ejecucion para consultas incrementales
    ahora = timezone.now()

    # Determinar "desde" para consulta incremental
    if tarea_config.ultima_ejecucion:
        # Ya se ejecutó antes: traer solo desde la última ejecución + 1 segundo
        desde = (tarea_config.ultima_ejecucion + timedelta(seconds=1)).isoformat()
        logger.info(f"[TareaPersonalizada] Modo INCREMENTAL: desde última ejecución")
    elif tarea_config.fecha_desde:
        # Primera ejecución: usar fecha_desde configurada
        desde = tarea_config.fecha_desde.isoformat()
        logger.info(f"[TareaPersonalizada] Primera ejecución: usando fecha_desde configurada")
    else:
        # Sin fecha_desde ni última ejecución: traer todo
        desde = None
        logger.info(f"[TareaPersonalizada] Sin filtro de fecha: traer todos los registros")

    # Determinar "hasta"
    hasta = tarea_config.fecha_hasta.isoformat() if tarea_config.fecha_hasta else ahora.isoformat()

    logger.info(f"[TareaPersonalizada] Ingesta {tipo_ingesta}: desde={desde}, hasta={hasta}")

    # Si se debe respetar rate limits, crear tarea en cola
    if tarea_config.respetar_rate_limits:
        # Mapear a tipo de tarea
        tipo_tarea_map = {
            'preinscriptos': Tarea.TipoTarea.INGESTA_PREINSCRIPTOS,
            'aspirantes': Tarea.TipoTarea.INGESTA_ASPIRANTES,
            'ingresantes': Tarea.TipoTarea.INGESTA_INGRESANTES,
        }

        # Crear tarea en cola PENDING
        tarea = Tarea.objects.create(
            tipo=tipo_tarea_map[tipo_ingesta],
            estado=Tarea.EstadoTarea.PENDING,
            celery_task_id=None,  # Se asignará cuando el procesador la tome
            detalles={
                'tarea_personalizada_id': tarea_config.id,
                'desde': desde,
                'hasta': hasta,
                'enviar_email': tarea_config.enviar_email,
                'origen': 'tarea_personalizada'
            }
        )

        logger.info(f"[TareaPersonalizada] ✅ Tarea {tarea.id} creada en cola (PENDING)")
        return {
            'success': True,
            'mensaje': f'Tarea encolada (ID: {tarea.id})',
            'tarea_id': tarea.id,
            'en_cola': True
        }

    else:
        # Ejecutar directamente sin rate limits
        tarea = Tarea.objects.create(
            tipo=tipo_tarea_map[tipo_ingesta],
            estado=Tarea.EstadoTarea.RUNNING,
            celery_task_id=celery_task_id,
            hora_inicio=timezone.now(),
            detalles={'desde': desde, 'hasta': hasta, 'origen': 'tarea_personalizada'}
        )

        try:
            created, updated, errors, nuevos_ids = ingerir_desde_sial(
                tipo=tipo_ingesta,
                desde=desde,
                hasta=hasta,
                retornar_nuevos=True,
                enviar_email=tarea_config.enviar_email
            )

            tarea.estado = Tarea.EstadoTarea.COMPLETED
            tarea.cantidad_entidades = created + updated
            tarea.hora_fin = timezone.now()
            tarea.detalles.update({
                'created': created,
                'updated': updated,
                'errors': len(errors)
            })
            tarea.save()

            return {
                'success': True,
                'created': created,
                'updated': updated,
                'errors': len(errors),
                'tarea_id': tarea.id
            }

        except Exception as e:
            tarea.estado = Tarea.EstadoTarea.FAILED
            tarea.mensaje_error = str(e)
            tarea.hora_fin = timezone.now()
            tarea.save()
            raise


def _ejecutar_accion_sobre_alumnos(tarea_config, celery_task_id):
    """
    Ejecuta una acción sobre alumnos según filtros de TareaPersonalizada.
    """
    from .models import Alumno, Tarea

    # Filtrar alumnos según tipo
    queryset = Alumno.objects.all()
    if tarea_config.tipo_usuario != 'todos':
        queryset = queryset.filter(estado_actual=tarea_config.tipo_usuario)

    alumnos = list(queryset)
    logger.info(f"[TareaPersonalizada] Encontrados {len(alumnos)} alumnos para procesar")

    if not alumnos:
        return {'success': True, 'mensaje': 'No hay alumnos para procesar', 'procesados': 0}

    # Mapear acción a tipo de tarea
    accion_to_tipo = {
        'crear_usuario_teams': Tarea.TipoTarea.CREAR_USUARIO_TEAMS,
        'enviar_email': Tarea.TipoTarea.ENVIAR_EMAIL,
        'activar_servicios': Tarea.TipoTarea.ACTIVAR_SERVICIOS,
        'moodle_enroll': Tarea.TipoTarea.MOODLE_ENROLL,
        'resetear_password': Tarea.TipoTarea.RESETEAR_PASSWORD,
    }

    tipo_tarea = accion_to_tipo.get(tarea_config.accion)

    # Crear tareas en cola para cada alumno
    tareas_creadas = []
    for alumno in alumnos:
        tarea = Tarea.objects.create(
            tipo=tipo_tarea,
            estado=Tarea.EstadoTarea.PENDING,
            alumno=alumno,
            detalles={
                'tarea_personalizada_id': tarea_config.id,
                'origen': 'tarea_personalizada'
            }
        )
        tareas_creadas.append(tarea.id)

    logger.info(f"[TareaPersonalizada] ✅ {len(tareas_creadas)} tareas creadas en cola")

    return {
        'success': True,
        'mensaje': f'{len(tareas_creadas)} tareas encoladas',
        'tareas_creadas': tareas_creadas,
        'procesados': len(tareas_creadas)
    }
