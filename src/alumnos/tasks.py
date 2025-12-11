"""
Tareas asíncronas de Celery para alumnos.
"""
import logging
from datetime import datetime
from celery import shared_task
from django.utils import timezone
from .models import Configuracion, Log, Tarea, Alumno
from .services import ingerir_desde_sial
from .services.teams_service import TeamsService
from .services.email_service import EmailService

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def ingestar_preinscriptos(self):
    """
    Tarea programada para ingestar preinscriptos desde SIAL.
    Se ejecuta según la configuración en BD.
    """
    config = Configuracion.load()

    # Verificar si está habilitada la ingesta
    if not config.preinscriptos_dia_inicio:
        logger.info("Ingesta de preinscriptos deshabilitada (dia_inicio vacío)")
        return

    # Verificar rango de fechas
    ahora = timezone.now()

    if ahora < config.preinscriptos_dia_inicio:
        logger.info(f"Fuera de rango: {ahora} < {config.preinscriptos_dia_inicio}")
        return

    if config.preinscriptos_dia_fin and ahora > config.preinscriptos_dia_fin:
        logger.info(f"Fuera de rango: {ahora} > {config.preinscriptos_dia_fin}")
        return

    # Crear registro de tarea
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.INGESTA_PREINSCRIPTOS,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        hora_inicio=timezone.now()
    )

    # Ejecutar ingesta
    try:
        logger.info("Iniciando ingesta automática de preinscriptos")
        created, updated, errors, nuevos_ids = ingerir_desde_sial(tipo='preinscriptos', retornar_nuevos=True)

        # Actualizar tarea
        tarea.estado = Tarea.EstadoTarea.COMPLETED
        tarea.cantidad_entidades = created + updated
        tarea.hora_fin = timezone.now()
        tarea.detalles = {
            'created': created,
            'updated': updated,
            'errors': len(errors),
            'nuevos_procesados': len(nuevos_ids) if nuevos_ids else 0
        }
        tarea.save()

        Log.objects.create(
            tipo='SUCCESS',
            modulo='tasks',
            mensaje=f'Ingesta automática de preinscriptos: {created} creados, {updated} actualizados',
            detalles={'created': created, 'updated': updated, 'errors': len(errors)}
        )

        logger.info(f"Ingesta completada: {created} creados, {updated} actualizados, {len(errors)} errores")

        # Procesar alumnos nuevos en lotes (Teams + Moodle + Email)
        if nuevos_ids and len(nuevos_ids) > 0:
            batch_size = config.batch_size
            logger.info(f"Detectados {len(nuevos_ids)} alumnos nuevos, lanzando workflow en lotes de {batch_size}")

            # Dividir en lotes
            for i in range(0, len(nuevos_ids), batch_size):
                lote = nuevos_ids[i:i + batch_size]
                logger.info(f"Lanzando lote {i//batch_size + 1}: {len(lote)} alumnos")
                procesar_lote_alumnos_nuevos.delay(lote, 'preinscripto')

        return {'created': created, 'updated': updated, 'errors': len(errors), 'nuevos': len(nuevos_ids) if nuevos_ids else 0}

    except Exception as e:
        logger.error(f"Error en ingesta automática de preinscriptos: {e}")

        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = str(e)
        tarea.hora_fin = timezone.now()
        tarea.save()

        Log.objects.create(
            tipo='ERROR',
            modulo='tasks',
            mensaje=f'Error en ingesta automática de preinscriptos',
            detalles={'error': str(e)}
        )
        raise


@shared_task(bind=True)
def ingestar_aspirantes(self):
    """Tarea programada para ingestar aspirantes desde SIAL."""
    config = Configuracion.load()

    if not config.aspirantes_dia_inicio:
        logger.info("Ingesta de aspirantes deshabilitada")
        return

    ahora = timezone.now()

    if ahora < config.aspirantes_dia_inicio:
        logger.info(f"Fuera de rango: {ahora} < {config.aspirantes_dia_inicio}")
        return

    if config.aspirantes_dia_fin and ahora > config.aspirantes_dia_fin:
        logger.info(f"Fuera de rango: {ahora} > {config.aspirantes_dia_fin}")
        return

    # Crear registro de tarea
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.INGESTA_ASPIRANTES,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        hora_inicio=timezone.now()
    )

    try:
        logger.info("Iniciando ingesta automática de aspirantes")
        created, updated, errors, nuevos_ids = ingerir_desde_sial(tipo='aspirantes', retornar_nuevos=True)

        # Actualizar tarea
        tarea.estado = Tarea.EstadoTarea.COMPLETED
        tarea.cantidad_entidades = created + updated
        tarea.hora_fin = timezone.now()
        tarea.detalles = {
            'created': created,
            'updated': updated,
            'errors': len(errors),
            'nuevos_procesados': len(nuevos_ids) if nuevos_ids else 0
        }
        tarea.save()

        Log.objects.create(
            tipo='SUCCESS',
            modulo='tasks',
            mensaje=f'Ingesta automática de aspirantes: {created} creados, {updated} actualizados',
            detalles={'created': created, 'updated': updated, 'errors': len(errors)}
        )

        logger.info(f"Ingesta completada: {created} creados, {updated} actualizados, {len(errors)} errores")

        # Procesar alumnos nuevos en lotes (Teams + Moodle + Email)
        if nuevos_ids and len(nuevos_ids) > 0:
            batch_size = config.batch_size
            logger.info(f"Detectados {len(nuevos_ids)} aspirantes nuevos, lanzando workflow en lotes de {batch_size}")

            # Dividir en lotes
            for i in range(0, len(nuevos_ids), batch_size):
                lote = nuevos_ids[i:i + batch_size]
                logger.info(f"Lanzando lote {i//batch_size + 1}: {len(lote)} aspirantes")
                procesar_lote_alumnos_nuevos.delay(lote, 'aspirante')

        return {'created': created, 'updated': updated, 'errors': len(errors), 'nuevos': len(nuevos_ids) if nuevos_ids else 0}

    except Exception as e:
        logger.error(f"Error en ingesta automática de aspirantes: {e}")

        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = str(e)
        tarea.hora_fin = timezone.now()
        tarea.save()

        Log.objects.create(
            tipo='ERROR',
            modulo='tasks',
            mensaje=f'Error en ingesta automática de aspirantes',
            detalles={'error': str(e)}
        )
        raise


@shared_task(bind=True)
def ingestar_ingresantes(self):
    """Tarea programada para ingestar ingresantes desde SIAL."""
    config = Configuracion.load()

    if not config.ingresantes_dia_inicio:
        logger.info("Ingesta de ingresantes deshabilitada")
        return

    ahora = timezone.now()

    if ahora < config.ingresantes_dia_inicio:
        logger.info(f"Fuera de rango: {ahora} < {config.ingresantes_dia_inicio}")
        return

    if config.ingresantes_dia_fin and ahora > config.ingresantes_dia_fin:
        logger.info(f"Fuera de rango: {ahora} > {config.ingresantes_dia_fin}")
        return

    # Crear registro de tarea
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.INGESTA_INGRESANTES,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        hora_inicio=timezone.now()
    )

    try:
        logger.info("Iniciando ingesta automática de ingresantes")
        created, updated, errors, nuevos_ids = ingerir_desde_sial(tipo='ingresantes', retornar_nuevos=True)

        # Actualizar tarea
        tarea.estado = Tarea.EstadoTarea.COMPLETED
        tarea.cantidad_entidades = created + updated
        tarea.hora_fin = timezone.now()
        tarea.detalles = {
            'created': created,
            'updated': updated,
            'errors': len(errors),
            'nuevos_procesados': len(nuevos_ids) if nuevos_ids else 0
        }
        tarea.save()

        Log.objects.create(
            tipo='SUCCESS',
            modulo='tasks',
            mensaje=f'Ingesta automática de ingresantes: {created} creados, {updated} actualizados',
            detalles={'created': created, 'updated': updated, 'errors': len(errors)}
        )

        logger.info(f"Ingesta completada: {created} creados, {updated} actualizados, {len(errors)} errores")

        # Procesar alumnos nuevos en lotes (Teams + Moodle + Email)
        if nuevos_ids and len(nuevos_ids) > 0:
            batch_size = config.batch_size
            logger.info(f"Detectados {len(nuevos_ids)} ingresantes nuevos, lanzando workflow en lotes de {batch_size}")

            # Dividir en lotes
            for i in range(0, len(nuevos_ids), batch_size):
                lote = nuevos_ids[i:i + batch_size]
                logger.info(f"Lanzando lote {i//batch_size + 1}: {len(lote)} ingresantes")
                procesar_lote_alumnos_nuevos.delay(lote, 'ingresante')

        return {'created': created, 'updated': updated, 'errors': len(errors), 'nuevos': len(nuevos_ids) if nuevos_ids else 0}

    except Exception as e:
        logger.error(f"Error en ingesta automática de ingresantes: {e}")

        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = str(e)
        tarea.hora_fin = timezone.now()
        tarea.save()

        Log.objects.create(
            tipo='ERROR',
            modulo='tasks',
            mensaje=f'Error en ingesta automática de ingresantes',
            detalles={'error': str(e)}
        )
        raise


@shared_task
def activar_servicios_alumno(alumno_id):
    """
    Tarea asíncrona para activar Teams + Email para un alumno.

    Args:
        alumno_id: ID del alumno
    """
    from .models import Alumno

    try:
        alumno = Alumno.objects.get(id=alumno_id)
    except Alumno.DoesNotExist:
        logger.error(f"Alumno {alumno_id} no encontrado")
        return

    teams_svc = TeamsService()
    email_svc = EmailService()

    # 1. Crear usuario en Teams
    teams_result = teams_svc.create_user(alumno)

    if not teams_result or not teams_result.get('created'):
        logger.error(f"Error creando usuario Teams para alumno {alumno_id}")
        return

    # 2. Enviar email
    email_sent = email_svc.send_credentials_email(alumno, teams_result)

    if email_sent:
        logger.info(f"Servicios activados para alumno {alumno_id}")
    else:
        logger.warning(f"Usuario creado pero email no enviado para alumno {alumno_id}")


@shared_task(bind=True)
def eliminar_cuenta_externa(self, alumno_id, upn):
    """
    Tarea asíncrona para eliminar cuenta de Teams y Moodle de un alumno.

    Args:
        alumno_id: ID del alumno
        upn: User Principal Name (email institucional)
    """
    # Crear registro de tarea
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.ELIMINAR_CUENTA,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        alumno_id=alumno_id,
        hora_inicio=timezone.now(),
        detalles={'upn': upn}
    )

    try:
        # Verificación de seguridad: solo eliminar cuentas test-*
        if not upn.startswith('test-'):
            mensaje = f"SEGURIDAD: Intento de eliminar cuenta NO-TEST bloqueado: {upn}"
            logger.warning(mensaje)

            tarea.estado = Tarea.EstadoTarea.FAILED
            tarea.mensaje_error = mensaje
            tarea.hora_fin = timezone.now()
            tarea.save()

            Log.objects.create(
                tipo='WARNING',
                modulo='tasks',
                mensaje=mensaje,
                detalles={'upn': upn, 'alumno_id': alumno_id}
            )
            return {'success': False, 'error': 'Cuenta no-test bloqueada'}

        # Eliminar de Teams
        teams_svc = TeamsService()
        teams_result = teams_svc.delete_user(upn)

        if teams_result:
            logger.info(f"Usuario Teams eliminado: {upn}")
            Log.objects.create(
                tipo='SUCCESS',
                modulo='tasks',
                mensaje=f'Usuario Teams eliminado: {upn}',
                detalles={'upn': upn}
            )
        else:
            logger.warning(f"No se pudo eliminar usuario Teams: {upn}")

        # TODO: Eliminar de Moodle cuando esté implementado
        # moodle_svc = MoodleService()
        # moodle_svc.delete_user(username)

        # Marcar tarea como completada
        tarea.estado = Tarea.EstadoTarea.COMPLETED
        tarea.cantidad_entidades = 1
        tarea.hora_fin = timezone.now()
        tarea.detalles['teams_deleted'] = teams_result
        tarea.save()

        return {'success': True, 'upn': upn}

    except Exception as e:
        logger.error(f"Error eliminando cuenta externa {upn}: {e}")

        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = str(e)
        tarea.hora_fin = timezone.now()
        tarea.save()

        Log.objects.create(
            tipo='ERROR',
            modulo='tasks',
            mensaje=f'Error eliminando cuenta externa: {upn}',
            detalles={'upn': upn, 'error': str(e)}
        )
        raise


@shared_task(bind=True)
def enviar_email_credenciales(self, alumno_id, teams_data):
    """
    Tarea asíncrona para enviar email con credenciales a un alumno.

    Args:
        alumno_id: ID del alumno
        teams_data: Datos de Teams (upn, password, etc.)
    """
    # Crear registro de tarea
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.ENVIAR_EMAIL,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        alumno_id=alumno_id,
        hora_inicio=timezone.now()
    )

    try:
        alumno = Alumno.objects.get(id=alumno_id)
    except Alumno.DoesNotExist:
        logger.error(f"Alumno {alumno_id} no encontrado")

        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = f"Alumno {alumno_id} no encontrado"
        tarea.hora_fin = timezone.now()
        tarea.save()
        return {'success': False, 'error': 'Alumno no encontrado'}

    try:
        email_svc = EmailService()
        email_sent = email_svc.send_credentials_email(alumno, teams_data)

        if email_sent:
            logger.info(f"Email enviado a {alumno.email}")

            tarea.estado = Tarea.EstadoTarea.COMPLETED
            tarea.cantidad_entidades = 1
            tarea.hora_fin = timezone.now()
            tarea.detalles = {'email': alumno.email, 'upn': teams_data.get('upn')}
            tarea.save()

            return {'success': True, 'email': alumno.email}
        else:
            mensaje = f"No se pudo enviar email a {alumno.email}"
            logger.warning(mensaje)

            tarea.estado = Tarea.EstadoTarea.FAILED
            tarea.mensaje_error = mensaje
            tarea.hora_fin = timezone.now()
            tarea.save()

            return {'success': False, 'error': 'Email no enviado'}

    except Exception as e:
        logger.error(f"Error enviando email a alumno {alumno_id}: {e}")

        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = str(e)
        tarea.hora_fin = timezone.now()
        tarea.save()

        Log.objects.create(
            tipo='ERROR',
            modulo='tasks',
            mensaje=f'Error enviando email a {alumno.email}',
            detalles={'alumno_id': alumno_id, 'error': str(e)}
        )
        raise


@shared_task(bind=True)
def crear_usuario_teams_async(self, alumno_id):
    """
    Tarea asíncrona para crear usuario en Teams (sin enviar email).

    Args:
        alumno_id: ID del alumno
    """
    # Crear registro de tarea
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.CREAR_USUARIO_TEAMS,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        alumno_id=alumno_id,
        hora_inicio=timezone.now()
    )

    try:
        alumno = Alumno.objects.get(id=alumno_id)
    except Alumno.DoesNotExist:
        logger.error(f"Alumno {alumno_id} no encontrado")

        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = f"Alumno {alumno_id} no encontrado"
        tarea.hora_fin = timezone.now()
        tarea.save()
        return {'success': False, 'error': 'Alumno no encontrado'}

    try:
        teams_svc = TeamsService()
        teams_result = teams_svc.create_user(alumno)

        if teams_result and teams_result.get('created'):
            logger.info(f"Usuario Teams creado: {teams_result.get('upn')}")

            tarea.estado = Tarea.EstadoTarea.COMPLETED
            tarea.cantidad_entidades = 1
            tarea.hora_fin = timezone.now()
            tarea.detalles = {
                'upn': teams_result.get('upn'),
                'password': teams_result.get('password')
            }
            tarea.save()

            return {
                'success': True,
                'upn': teams_result.get('upn'),
                'password': teams_result.get('password')
            }
        else:
            mensaje = teams_result.get('error', 'Error desconocido')
            logger.warning(f"No se pudo crear usuario Teams: {mensaje}")

            tarea.estado = Tarea.EstadoTarea.FAILED
            tarea.mensaje_error = mensaje
            tarea.hora_fin = timezone.now()
            tarea.save()

            return {'success': False, 'error': mensaje}

    except Exception as e:
        logger.error(f"Error creando usuario Teams para alumno {alumno_id}: {e}")

        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = str(e)
        tarea.hora_fin = timezone.now()
        tarea.save()

        Log.objects.create(
            tipo='ERROR',
            modulo='tasks',
            mensaje=f'Error creando usuario Teams',
            detalles={'alumno_id': alumno_id, 'error': str(e)}
        )
        raise


@shared_task(bind=True)
def resetear_password_y_enviar_email(self, alumno_id):
    """
    Tarea asíncrona para resetear contraseña de Teams y enviar email.

    Args:
        alumno_id: ID del alumno
    """
    from django.conf import settings

    # Crear registro de tarea
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.RESETEAR_PASSWORD,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        alumno_id=alumno_id,
        hora_inicio=timezone.now()
    )

    try:
        alumno = Alumno.objects.get(id=alumno_id)
    except Alumno.DoesNotExist:
        logger.error(f"Alumno {alumno_id} no encontrado")

        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = f"Alumno {alumno_id} no encontrado"
        tarea.hora_fin = timezone.now()
        tarea.save()
        return {'success': False, 'error': 'Alumno no encontrado'}

    try:
        teams_svc = TeamsService()
        email_svc = EmailService()

        # Construir UPN
        prefix = settings.ACCOUNT_PREFIX
        upn = f"{prefix}{alumno.dni}@{settings.TEAMS_DOMAIN}"

        # 1. Verificar que el usuario existe
        user = teams_svc.get_user(upn)
        if not user:
            mensaje = f"Usuario {upn} no existe en Teams"
            logger.warning(mensaje)

            tarea.estado = Tarea.EstadoTarea.FAILED
            tarea.mensaje_error = mensaje
            tarea.hora_fin = timezone.now()
            tarea.save()

            return {'success': False, 'error': mensaje}

        # 2. Resetear contraseña
        new_password = teams_svc.reset_password(upn)
        if not new_password:
            mensaje = "Error reseteando contraseña"
            logger.error(mensaje)

            tarea.estado = Tarea.EstadoTarea.FAILED
            tarea.mensaje_error = mensaje
            tarea.hora_fin = timezone.now()
            tarea.save()

            return {'success': False, 'error': mensaje}

        # Actualizar alumno
        alumno.email_institucional = upn
        alumno.teams_password = new_password
        alumno.save(update_fields=['email_institucional', 'teams_password'])

        # 3. Enviar email
        teams_data = {
            'upn': upn,
            'password': new_password,
            'created': False
        }

        email_sent = email_svc.send_credentials_email(alumno, teams_data)

        if email_sent:
            logger.info(f"Contraseña reseteada y email enviado a {alumno.email}")

            tarea.estado = Tarea.EstadoTarea.COMPLETED
            tarea.cantidad_entidades = 1
            tarea.hora_fin = timezone.now()
            tarea.detalles = {'upn': upn, 'email': alumno.email}
            tarea.save()

            return {'success': True, 'upn': upn, 'email': alumno.email}
        else:
            mensaje = "Contraseña reseteada pero error enviando email"
            logger.warning(mensaje)

            tarea.estado = Tarea.EstadoTarea.COMPLETED
            tarea.cantidad_entidades = 1
            tarea.hora_fin = timezone.now()
            tarea.mensaje_error = mensaje
            tarea.detalles = {'upn': upn, 'password_reset': True, 'email_sent': False}
            tarea.save()

            return {'success': True, 'upn': upn, 'warning': 'Email no enviado'}

    except Exception as e:
        logger.error(f"Error reseteando contraseña para alumno {alumno_id}: {e}")

        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = str(e)
        tarea.hora_fin = timezone.now()
        tarea.save()

        Log.objects.create(
            tipo='ERROR',
            modulo='tasks',
            mensaje=f'Error reseteando contraseña',
            detalles={'alumno_id': alumno_id, 'error': str(e)}
        )
        raise


@shared_task(bind=True)
def procesar_alumno_nuevo_completo(self, alumno_id, estado):
    """
    Workflow completo para alumno nuevo:
    1. Crear cuenta en Teams
    2. Asignar licencia
    3. Enrolar en Moodle (TODO)
    4. Enviar email de bienvenida

    Args:
        alumno_id: ID del alumno
        estado: Estado del alumno (preinscripto, aspirante, ingresante)

    Rate limiting: Controlado por batch_size y rate_limit_teams/moodle en Configuracion
    """
    # Crear registro de tarea
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.ACTIVAR_SERVICIOS,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        alumno_id=alumno_id,
        hora_inicio=timezone.now(),
        detalles={'estado': estado, 'workflow': 'completo'}
    )

    try:
        alumno = Alumno.objects.get(id=alumno_id)
    except Alumno.DoesNotExist:
        logger.error(f"Alumno {alumno_id} no encontrado")
        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = f"Alumno {alumno_id} no encontrado"
        tarea.hora_fin = timezone.now()
        tarea.save()
        return {'success': False, 'error': 'Alumno no encontrado'}

    resultados = {
        'teams': False,
        'moodle': False,
        'email': False,
        'errores': []
    }

    try:
        # 1. Crear usuario en Teams
        logger.info(f"[Workflow] Paso 1/3: Creando usuario Teams para {alumno}")
        teams_svc = TeamsService()
        teams_result = teams_svc.create_user(alumno)

        if teams_result and teams_result.get('created'):
            resultados['teams'] = True
            logger.info(f"[Workflow] ✓ Teams creado: {teams_result.get('upn')}")
        else:
            error_msg = teams_result.get('error', 'Error desconocido')
            resultados['errores'].append(f"Teams: {error_msg}")
            logger.warning(f"[Workflow] ✗ Teams falló: {error_msg}")

            # Si no podemos crear Teams, abortar workflow
            raise Exception(f"No se pudo crear cuenta Teams: {error_msg}")

        # 2. Enrolar en Moodle
        logger.info(f"[Workflow] Paso 2/3: Enrolando en Moodle para {alumno}")
        # TODO: Implementar cuando MoodleService esté listo
        # moodle_svc = MoodleService()
        # moodle_result = moodle_svc.enroll_user(alumno, cursos_segun_estado(estado))
        # if moodle_result:
        #     resultados['moodle'] = True
        logger.info(f"[Workflow] ⏸️  Moodle pendiente de implementar")
        resultados['moodle'] = 'pending'

        # 3. Enviar email de bienvenida
        logger.info(f"[Workflow] Paso 3/3: Enviando email para {alumno}")
        email_svc = EmailService()
        email_sent = email_svc.send_credentials_email(alumno, teams_result)

        if email_sent:
            resultados['email'] = True
            logger.info(f"[Workflow] ✓ Email enviado a {alumno.email}")
        else:
            resultados['errores'].append("Email: No se pudo enviar")
            logger.warning(f"[Workflow] ✗ Email no enviado")

        # Workflow completado (aunque email haya fallado, Teams está ok)
        tarea.estado = Tarea.EstadoTarea.COMPLETED
        tarea.cantidad_entidades = 1
        tarea.hora_fin = timezone.now()
        tarea.detalles = {
            'estado': estado,
            'workflow': 'completo',
            'resultados': resultados,
            'upn': teams_result.get('upn')
        }
        tarea.save()

        logger.info(f"[Workflow] ✓ Completado para {alumno}: {resultados}")
        return {'success': True, 'resultados': resultados}

    except Exception as e:
        logger.error(f"[Workflow] Error en workflow para alumno {alumno_id}: {e}")

        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = str(e)
        tarea.hora_fin = timezone.now()
        tarea.detalles = {
            'estado': estado,
            'workflow': 'completo',
            'resultados': resultados,
            'error': str(e)
        }
        tarea.save()

        Log.objects.create(
            tipo='ERROR',
            modulo='tasks',
            mensaje=f'Error en workflow completo para alumno',
            detalles={'alumno_id': alumno_id, 'estado': estado, 'error': str(e)}
        )
        raise


@shared_task(bind=True)
def procesar_lote_alumnos_nuevos(self, alumno_ids, estado):
    """
    Procesa un lote de alumnos nuevos con rate limiting manual.

    Args:
        alumno_ids: Lista de IDs de alumnos a procesar
        estado: Estado de los alumnos (preinscripto, aspirante, ingresante)

    Esta tarea procesa alumnos uno por uno respetando el rate limit
    configurado en Configuracion.rate_limit_teams.
    """
    import time
    from .models import Configuracion

    config = Configuracion.load()
    rate_limit = config.rate_limit_teams  # tareas por minuto
    delay_seconds = 60.0 / rate_limit if rate_limit > 0 else 0

    logger.info(f"[Batch] Procesando lote de {len(alumno_ids)} alumnos ({estado}) con rate limit {rate_limit}/min")

    # Crear registro de tarea para el lote
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.ACTIVAR_SERVICIOS,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        hora_inicio=timezone.now(),
        detalles={
            'tipo': 'lote',
            'cantidad_alumnos': len(alumno_ids),
            'estado': estado,
            'rate_limit': rate_limit
        }
    )

    try:
        # Procesar alumnos uno por uno con rate limiting
        resultados = []
        for idx, alumno_id in enumerate(alumno_ids):
            logger.info(f"[Batch] Procesando {idx+1}/{len(alumno_ids)}: alumno_id={alumno_id}")

            # Ejecutar workflow síncronamente
            resultado = procesar_alumno_nuevo_completo(alumno_id, estado)
            resultados.append(resultado)

            # Rate limiting: Esperar antes del siguiente (excepto en el último)
            if idx < len(alumno_ids) - 1 and delay_seconds > 0:
                logger.debug(f"[Batch] Esperando {delay_seconds:.2f}s (rate limit)")
                time.sleep(delay_seconds)

        # Contar éxitos y fallos
        exitosos = sum(1 for r in resultados if r.get('success'))
        fallidos = len(alumno_ids) - exitosos

        # Actualizar tarea del lote
        tarea.estado = Tarea.EstadoTarea.COMPLETED
        tarea.cantidad_entidades = exitosos
        tarea.hora_fin = timezone.now()
        tarea.detalles = {
            'tipo': 'lote',
            'cantidad_alumnos': len(alumno_ids),
            'estado': estado,
            'exitosos': exitosos,
            'fallidos': fallidos
        }
        tarea.save()

        logger.info(f"[Batch] ✓ Lote completado: {exitosos} exitosos, {fallidos} fallidos")

        return {
            'success': True,
            'total': len(alumno_ids),
            'exitosos': exitosos,
            'fallidos': fallidos
        }

    except Exception as e:
        logger.error(f"[Batch] Error procesando lote: {e}")

        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = str(e)
        tarea.hora_fin = timezone.now()
        tarea.save()

        Log.objects.create(
            tipo='ERROR',
            modulo='tasks',
            mensaje=f'Error procesando lote de {len(alumno_ids)} alumnos',
            detalles={'estado': estado, 'error': str(e)}
        )
        raise
