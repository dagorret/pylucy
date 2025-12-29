"""
Nombre del Módulo: teams.py

Descripción:
Tareas relacionadas con Microsoft Teams (crear usuarios, resetear passwords, eliminar cuentas).

Autor: Carlos Dagorret
Fecha de Creación: 2025-12-29
Última Modificación: 2025-12-29

Licencia: MIT
Copyright (c) 2025 Carlos Dagorret
"""

import logging
from celery import shared_task
from django.utils import timezone
from ..models import Log, Tarea, Alumno
from ..services.teams_service import TeamsService
from ..services.email_service import EmailService

logger = logging.getLogger(__name__)


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
        prefix = teams_svc.account_prefix
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
