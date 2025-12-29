"""
Nombre del Módulo: procesamiento.py

Descripción:
Procesamiento de cola de tareas pendientes con rate limiting.

Autor: Carlos Dagorret
Fecha de Creación: 2025-12-29
Última Modificación: 2025-12-29

Licencia: MIT
Copyright (c) 2025 Carlos Dagorret
"""

import logging
import time
from collections import defaultdict
from celery import shared_task
from django.utils import timezone
from ..models import Configuracion, Tarea

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def procesar_cola_tareas_pendientes(self):
    """
    Procesa tareas pendientes en la cola respetando batch_size y rate_limits.

    Esta tarea se ejecuta cada 5 minutos vía Celery Beat y:
    1. Busca tareas con estado=PENDING
    2. Agrupa por tipo de tarea
    3. Procesa hasta batch_size tareas por ejecución
    4. Aplica rate limiting según el tipo de tarea

    **Arquitectura**:
    - Las acciones del admin crean registros Tarea con estado=PENDING
    - Este procesador las toma en lotes y ejecuta respetando límites
    - Ver docs/ARQUITECTURA_COLAS.md para más detalles

    **Rate Limits** (configurables en modelo Configuracion):
    - rate_limit_teams: Tareas/minuto para Microsoft Teams/Graph API
    - rate_limit_moodle: Tareas/minuto para Moodle Web Services
    - rate_limit_uti: Tareas/minuto para API UTI/SIAL
    """
    import time
    from collections import defaultdict

    config = Configuracion.load()
    batch_size = config.batch_size

    logger.info(f"[Cola] Iniciando procesamiento de tareas pendientes (batch_size={batch_size})")

    # Buscar tareas pendientes (ordenadas por antigüedad)
    tareas_pending = Tarea.objects.filter(
        estado=Tarea.EstadoTarea.PENDING
    ).order_by('hora_programada')[:batch_size * 2]  # Traer más para asegurar batch completo

    if not tareas_pending.exists():
        logger.info("[Cola] No hay tareas pendientes")
        return {'procesadas': 0, 'mensaje': 'No hay tareas pendientes'}

    # Agrupar por tipo de tarea
    tareas_por_tipo = defaultdict(list)
    contador_total = 0

    for tarea in tareas_pending:
        if contador_total >= batch_size:
            break
        tareas_por_tipo[tarea.tipo].append(tarea)
        contador_total += 1

    logger.info(f"[Cola] Encontradas {contador_total} tareas pendientes agrupadas en {len(tareas_por_tipo)} tipos")

    # Procesar cada tipo con su rate limit correspondiente
    resultados = {}
    for tipo_tarea, tareas in tareas_por_tipo.items():
        logger.info(f"[Cola] Procesando {len(tareas)} tareas de tipo '{tipo_tarea}'")

        resultado = procesar_lote_por_tipo_tarea(
            tareas=tareas,
            tipo_tarea=tipo_tarea,
            config=config
        )

        resultados[tipo_tarea] = resultado

    # Resumen final
    total_exitosas = sum(r.get('exitosas', 0) for r in resultados.values())
    total_fallidas = sum(r.get('fallidas', 0) for r in resultados.values())

    logger.info(
        f"[Cola] Procesamiento finalizado: {total_exitosas} exitosas, "
        f"{total_fallidas} fallidas de {contador_total} tareas"
    )

    return {
        'procesadas': contador_total,
        'exitosas': total_exitosas,
        'fallidas': total_fallidas,
        'por_tipo': resultados
    }


def procesar_lote_por_tipo_tarea(tareas, tipo_tarea, config):
    """
    Procesa un lote de tareas del mismo tipo aplicando rate limiting.

    Args:
        tareas: Lista de objetos Tarea con el mismo tipo
        tipo_tarea: String con el tipo (ej: 'crear_usuario_teams')
        config: Objeto Configuracion con rate_limits

    Returns:
        Dict con estadísticas: {'exitosas': int, 'fallidas': int, 'errores': []}
    """
    import time

    # Determinar rate limit según tipo de tarea
    rate_limit_map = {
        # Tareas de Teams/Graph API
        Tarea.TipoTarea.CREAR_USUARIO_TEAMS: config.rate_limit_teams,
        Tarea.TipoTarea.RESETEAR_PASSWORD: config.rate_limit_teams,
        Tarea.TipoTarea.ENVIAR_EMAIL: config.rate_limit_teams,

        # Tareas de Moodle
        Tarea.TipoTarea.MOODLE_ENROLL: config.rate_limit_moodle,

        # Tareas de UTI/SIAL
        Tarea.TipoTarea.INGESTA_PREINSCRIPTOS: config.rate_limit_uti,
        Tarea.TipoTarea.INGESTA_ASPIRANTES: config.rate_limit_uti,
        Tarea.TipoTarea.INGESTA_INGRESANTES: config.rate_limit_uti,

        # Tareas mixtas (usan el menor rate limit para seguridad)
        Tarea.TipoTarea.ACTIVAR_SERVICIOS: min(config.rate_limit_teams, config.rate_limit_moodle),
        Tarea.TipoTarea.ELIMINAR_CUENTA: min(config.rate_limit_teams, config.rate_limit_moodle),
    }

    rate_limit = rate_limit_map.get(tipo_tarea, 10)  # Default 10 tareas/min
    delay_seconds = 60.0 / rate_limit if rate_limit > 0 else 0

    logger.info(
        f"[Cola:{tipo_tarea}] Procesando {len(tareas)} tareas con rate limit "
        f"{rate_limit}/min (delay={delay_seconds:.2f}s)"
    )

    exitosas = 0
    fallidas = 0
    errores = []

    for idx, tarea in enumerate(tareas):
        try:
            # Marcar como RUNNING
            tarea.estado = Tarea.EstadoTarea.RUNNING
            tarea.hora_inicio = timezone.now()
            tarea.save(update_fields=['estado', 'hora_inicio'])

            # Ejecutar la tarea según su tipo
            resultado = ejecutar_tarea_segun_tipo(tarea)

            # Marcar como COMPLETED o FAILED
            if resultado.get('success'):
                tarea.estado = Tarea.EstadoTarea.COMPLETED
                tarea.detalles = resultado.get('detalles', {})
                tarea.cantidad_entidades = resultado.get('cantidad_entidades', 1)
                exitosas += 1
            else:
                tarea.estado = Tarea.EstadoTarea.FAILED
                tarea.mensaje_error = resultado.get('error', 'Error desconocido')
                tarea.detalles = resultado.get('detalles', {})
                fallidas += 1
                errores.append({
                    'tarea_id': tarea.id,
                    'error': tarea.mensaje_error
                })

            tarea.hora_fin = timezone.now()
            tarea.save()

            logger.info(
                f"[Cola:{tipo_tarea}] Tarea {tarea.id} procesada "
                f"({'OK' if resultado.get('success') else 'FAIL'}) "
                f"[{idx+1}/{len(tareas)}]"
            )

        except Exception as e:
            # Error inesperado al procesar la tarea
            logger.error(f"[Cola:{tipo_tarea}] Error procesando tarea {tarea.id}: {e}", exc_info=True)

            tarea.estado = Tarea.EstadoTarea.FAILED
            tarea.mensaje_error = f"Error inesperado: {str(e)}"
            tarea.hora_fin = timezone.now()
            tarea.save()

            fallidas += 1
            errores.append({
                'tarea_id': tarea.id,
                'error': str(e)
            })

        # Rate limiting: Esperar antes del siguiente (excepto en el último)
        if idx < len(tareas) - 1 and delay_seconds > 0:
            logger.debug(f"[Cola:{tipo_tarea}] Esperando {delay_seconds:.2f}s (rate limit)")
            time.sleep(delay_seconds)

    return {
        'exitosas': exitosas,
        'fallidas': fallidas,
        'total': len(tareas),
        'errores': errores
    }


def ejecutar_tarea_segun_tipo(tarea):
    """
    Ejecuta una tarea según su tipo, llamando a la función correspondiente.

    Args:
        tarea: Objeto Tarea a ejecutar

    Returns:
        Dict con resultado: {'success': bool, 'detalles': dict, 'error': str}
    """
    try:
        # Mapeo de tipo de tarea a función ejecutora
        if tarea.tipo == Tarea.TipoTarea.CREAR_USUARIO_TEAMS:
            return ejecutar_crear_usuario_teams(tarea)

        elif tarea.tipo == Tarea.TipoTarea.RESETEAR_PASSWORD:
            return ejecutar_resetear_password(tarea)

        elif tarea.tipo == Tarea.TipoTarea.MOODLE_ENROLL:
            return ejecutar_enrollar_moodle(tarea)

        elif tarea.tipo == Tarea.TipoTarea.ACTIVAR_SERVICIOS:
            return ejecutar_activar_servicios(tarea)

        elif tarea.tipo == Tarea.TipoTarea.ELIMINAR_CUENTA:
            return ejecutar_eliminar_cuenta(tarea)

        elif tarea.tipo == Tarea.TipoTarea.ENVIAR_EMAIL:
            return ejecutar_enviar_email(tarea)

        else:
            return {
                'success': False,
                'error': f"Tipo de tarea no implementado: {tarea.tipo}"
            }

    except Exception as e:
        logger.error(f"Error ejecutando tarea {tarea.id} ({tarea.tipo}): {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'detalles': {'exception_type': type(e).__name__}
        }


# Funciones ejecutoras para cada tipo de tarea

def ejecutar_crear_usuario_teams(tarea):
    """
    Crea usuario en Teams para el alumno asociado a la tarea.
    Opcionalmente envía email con credenciales si detalles['enviar_email'] = True.
    """
    if not tarea.alumno:
        return {'success': False, 'error': 'Tarea sin alumno asociado'}

    from .services.teams_service import TeamsService
    from .services.email_service import EmailService

    teams_service = TeamsService()
    resultado = teams_service.create_user(tarea.alumno)

    # Interpretar resultado de create_user
    # create_user retorna: {'created': True/False, 'already_exists': True, ...} o None
    if resultado and ('created' in resultado or 'already_exists' in resultado):
        # Usuario creado o ya existía → ÉXITO
        # Marcar como procesado en Teams
        tarea.alumno.teams_procesado = True
        tarea.alumno.save(update_fields=['teams_procesado'])

        # Enviar email con credenciales si está habilitado
        enviar_email = tarea.detalles.get('enviar_email', False) if tarea.detalles else False
        email_enviado = False

        if enviar_email and resultado.get('password'):
            email_service = EmailService()
            teams_data = {
                'upn': resultado.get('upn'),
                'password': resultado.get('password')
            }
            email_enviado = email_service.send_credentials_email(tarea.alumno, teams_data)

            if email_enviado:
                tarea.alumno.email_procesado = True
                tarea.alumno.save(update_fields=['email_procesado'])

        return {
            'success': True,
            'detalles': {
                'upn': resultado.get('upn'),
                'user_id': resultado.get('id'),
                'created': resultado.get('created', False),
                'already_exists': resultado.get('already_exists', False),
                'email_enviado': email_enviado
            },
            'cantidad_entidades': 1
        }
    else:
        # Error o None
        error_msg = resultado.get('error') if resultado else 'Error desconocido creando usuario Teams'
        return {
            'success': False,
            'error': error_msg,
            'detalles': resultado if resultado else {}
        }


def ejecutar_resetear_password(tarea):
    """Resetea password de Teams y envía email al alumno."""
    if not tarea.alumno:
        return {'success': False, 'error': 'Tarea sin alumno asociado'}

    from .services.teams_service import TeamsService
    from .services.email_service import EmailService

    teams_service = TeamsService()
    email_service = EmailService()

    # Resetear password
    resultado_reset = teams_service.resetear_password_alumno(tarea.alumno)

    if not resultado_reset.get('success'):
        return {
            'success': False,
            'error': resultado_reset.get('error', 'Error reseteando password')
        }

    # Enviar email con nueva contraseña
    enviar_email = tarea.detalles.get('enviar_email', True) if tarea.detalles else True

    if enviar_email:
        email_service.enviar_email_password_reset(
            alumno=tarea.alumno,
            password=resultado_reset['password']
        )

    return {
        'success': True,
        'detalles': {'password_reset': True, 'email_enviado': enviar_email},
        'cantidad_entidades': 1
    }


def ejecutar_enrollar_moodle(tarea):
    """
    Enrolla alumno en cursos de Moodle según su estado.
    Opcionalmente envía email de enrollamiento si detalles['enviar_email'] = True.
    """
    if not tarea.alumno:
        return {'success': False, 'error': 'Tarea sin alumno asociado'}

    from .services.moodle_service import MoodleService

    moodle_service = MoodleService()
    enviar_email = tarea.detalles.get('enviar_email', False) if tarea.detalles else False

    resultado = moodle_service.enroll_user_in_courses(
        tarea.alumno,
        enviar_email=enviar_email
    )

    # Marcar como procesado en Moodle si fue exitoso
    if resultado.get('success'):
        tarea.alumno.moodle_procesado = True
        tarea.alumno.save(update_fields=['moodle_procesado'])

    return {
        'success': resultado.get('success', False),
        'error': resultado.get('error'),
        'detalles': resultado,
        'cantidad_entidades': len(resultado.get('enrolled_courses', []))
    }


def ejecutar_activar_servicios(tarea):
    """Activa servicios completos (Teams + Moodle + Email)."""
    if not tarea.alumno:
        return {'success': False, 'error': 'Tarea sin alumno asociado'}

    # Reutilizar función existente procesar_alumno_nuevo_completo
    estado = tarea.alumno.estado_workflow
    resultado = procesar_alumno_nuevo_completo(tarea.alumno.id, estado)

    return {
        'success': resultado.get('success', False),
        'error': resultado.get('error'),
        'detalles': resultado,
        'cantidad_entidades': 1
    }


def ejecutar_eliminar_cuenta(tarea):
    """Elimina cuenta de Teams y Moodle del alumno."""
    if not tarea.alumno:
        return {'success': False, 'error': 'Tarea sin alumno asociado'}

    # Reutilizar lógica de eliminar_cuenta_externa
    upn = tarea.alumno.email_institucional or tarea.detalles.get('upn')

    if not upn:
        return {'success': False, 'error': 'No se encontró UPN para eliminar'}

    from .services.teams_service import TeamsService
    from .services.moodle_service import MoodleService

    teams_service = TeamsService()
    moodle_service = MoodleService()

    errores = []

    # Eliminar de Teams
    resultado_teams = teams_service.eliminar_usuario(upn)
    if not resultado_teams.get('success'):
        errores.append(f"Teams: {resultado_teams.get('error')}")

    # Eliminar de Moodle
    resultado_moodle = moodle_service.eliminar_usuario(upn)
    if not resultado_moodle.get('success'):
        errores.append(f"Moodle: {resultado_moodle.get('error')}")

    if errores:
        return {
            'success': False,
            'error': '; '.join(errores),
            'detalles': {
                'teams': resultado_teams,
                'moodle': resultado_moodle
            }
        }

    return {
        'success': True,
        'detalles': {'teams': resultado_teams, 'moodle': resultado_moodle},
        'cantidad_entidades': 1
    }


def ejecutar_enviar_email(tarea):
    """Envía email según la configuración de la tarea."""
    if not tarea.alumno:
        return {'success': False, 'error': 'Tarea sin alumno asociado'}

    from .services.email_service import EmailService

    email_service = EmailService()
    tipo_email = tarea.detalles.get('tipo_email', 'credenciales') if tarea.detalles else 'credenciales'

    try:
        if tipo_email == 'bienvenida':
            email_service.enviar_email_bienvenida(tarea.alumno)
        elif tipo_email == 'credenciales':
            password = tarea.detalles.get('password', '***')
            email_service.enviar_email_credenciales(tarea.alumno, password)
        elif tipo_email == 'password_reset':
            password = tarea.detalles.get('password', '***')
            email_service.enviar_email_password_reset(tarea.alumno, password)
        else:
            return {'success': False, 'error': f'Tipo de email desconocido: {tipo_email}'}

        return {
            'success': True,
            'detalles': {'tipo_email': tipo_email},
            'cantidad_entidades': 1
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Error enviando email: {str(e)}'
        }


