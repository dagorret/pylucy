"""
Tareas de borrado para Teams y Moodle.
"""
import logging
from celery import shared_task
from django.utils import timezone
from .models import Log, Tarea

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def eliminar_solo_teams(self, alumno_id, upn):
    """
    Elimina usuario solo de Teams (no de Moodle).

    Args:
        alumno_id: ID del alumno
        upn: User Principal Name
    """
    from .services.teams_service import TeamsService
    from .models import Alumno

    # Verificación de seguridad
    if not upn.startswith('test-'):
        logger.error(f"SEGURIDAD: Intento de eliminar cuenta no-test: {upn}")
        return {'success': False, 'error': 'Cuenta no-test bloqueada'}

    teams_svc = TeamsService()
    result = teams_svc.delete_user(upn)

    if result:
        logger.info(f"✅ Usuario Teams eliminado: {upn}")

        # Actualizar flag del alumno
        try:
            alumno = Alumno.objects.get(id=alumno_id)
            alumno.teams_procesado = False
            alumno.save(update_fields=['teams_procesado'])
            logger.info(f"Flag teams_procesado actualizado a False para alumno {alumno_id}")
        except Alumno.DoesNotExist:
            logger.warning(f"Alumno {alumno_id} no encontrado para actualizar flag")

        Log.objects.create(
            tipo=Log.TipoLog.SUCCESS,
            modulo='eliminar_solo_teams',
            mensaje=f'Usuario Teams eliminado: {upn}',
            detalles={'upn': upn, 'alumno_id': alumno_id}
        )
        return {'success': True, 'upn': upn}
    else:
        logger.error(f"❌ Error eliminando usuario Teams: {upn}")
        Log.objects.create(
            tipo=Log.TipoLog.ERROR,
            modulo='eliminar_solo_teams',
            mensaje=f'Error eliminando usuario Teams: {upn}',
            detalles={'upn': upn, 'alumno_id': alumno_id}
        )
        return {'success': False, 'error': 'Error eliminando de Teams'}


@shared_task(bind=True)
def eliminar_solo_moodle(self, alumno_id, username):
    """
    Elimina usuario solo de Moodle (no de Teams).

    Args:
        alumno_id: ID del alumno
        username: Username de Moodle
    """
    from .services.moodle_service import MoodleService
    from .models import Alumno

    moodle_svc = MoodleService()
    result = moodle_svc.delete_user(username)

    if result:
        logger.info(f"✅ Usuario Moodle eliminado: {username}")

        # Actualizar flag del alumno
        try:
            alumno = Alumno.objects.get(id=alumno_id)
            alumno.moodle_procesado = False
            alumno.save(update_fields=['moodle_procesado'])
            logger.info(f"Flag moodle_procesado actualizado a False para alumno {alumno_id}")
        except Alumno.DoesNotExist:
            logger.warning(f"Alumno {alumno_id} no encontrado para actualizar flag")

        Log.objects.create(
            tipo=Log.TipoLog.SUCCESS,
            modulo='eliminar_solo_moodle',
            mensaje=f'Usuario Moodle eliminado: {username}',
            detalles={'username': username, 'alumno_id': alumno_id}
        )
        return {'success': True, 'username': username}
    else:
        logger.error(f"❌ Error eliminando usuario Moodle: {username}")
        Log.objects.create(
            tipo=Log.TipoLog.ERROR,
            modulo='eliminar_solo_moodle',
            mensaje=f'Error eliminando usuario Moodle: {username}',
            detalles={'username': username, 'alumno_id': alumno_id}
        )
        return {'success': False, 'error': 'Error eliminando de Moodle'}
