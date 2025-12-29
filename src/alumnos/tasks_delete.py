"""
Nombre del Módulo: tasks_delete.py

Descripción:
Tareas asíncronas de Celery para eliminación de cuentas.

Autor: Carlos Dagorret
Fecha de Creación: 2025-12-29
Última Modificación: 2025-12-29

Licencia: MIT
Copyright (c) 2025 Carlos Dagorret

Permisos:
Se concede permiso, de forma gratuita, a cualquier persona que obtenga una copia
de este software y la documentación asociada (el "Software"), para tratar
en el Software sin restricciones, incluyendo, sin limitación, los derechos
de usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar
y/o vender copias del Software, y para permitir a las personas a las que
se les proporciona el Software hacerlo, sujeto a las siguientes condiciones:

El aviso de copyright anterior y este aviso de permiso se incluirán en todas
las copias o partes sustanciales del Software.

EL SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍA DE NINGÚN TIPO, EXPRESA O
IMPLÍCITA, INCLUYENDO PERO NO LIMITADO A LAS GARANTÍAS DE COMERCIABILIDAD,
IDONEIDAD PARA UN PROPÓSITO PARTICULAR Y NO INFRACCIÓN. EN NINGÚN CASO LOS
AUTORES O TITULARES DE LOS DERECHOS DE AUTOR SERÁN RESPONSABLES DE CUALQUIER
RECLAMO, DAÑO U OTRA RESPONSABILIDAD, YA SEA EN UNA ACCIÓN DE CONTRATO,
AGRAVIO O DE OTRO MODO, QUE SURJA DE, FUERA DE O EN CONEXIÓN CON EL SOFTWARE
O EL USO U OTROS TRATOS EN EL SOFTWARE.
"""

import logging
from celery import shared_task
from django.utils import timezone
from .models import Log, Tarea, Alumno

logger = logging.getLogger(__name__)


def log_to_db(tipo, modulo, mensaje, detalles=None, alumno=None):
    """Registra un log en la base de datos."""
    try:
        Log.objects.create(
            tipo=tipo,
            modulo=modulo,
            mensaje=mensaje,
            detalles=detalles,
            alumno=alumno
        )
    except Exception as e:
        logger.error(f"Error guardando log en BD: {e}")


@shared_task(bind=True, max_retries=3)
def eliminar_solo_teams(self, alumno_id, upn):
    """
    Elimina usuario solo de Teams/Azure AD.

    - Marca teams_procesado=False
    - NO borra de Moodle
    - NO borra de base de datos

    Args:
        alumno_id: ID del alumno
        upn: User Principal Name del usuario en Teams
    """
    from .services.teams_service import TeamsService

    try:
        alumno = Alumno.objects.get(id=alumno_id)
        logger.info(f"[Borrar Teams] Iniciando borrado de {upn} (Alumno ID: {alumno_id})")

        # Crear registro de tarea
        tarea = Tarea.objects.create(
            tipo=Tarea.TipoTarea.ELIMINAR_CUENTA,
            estado=Tarea.EstadoTarea.RUNNING,
            celery_task_id=self.request.id,
            alumno=alumno,
            hora_inicio=timezone.now(),
            detalles={'accion': 'borrar_teams', 'upn': upn}
        )

        teams_svc = TeamsService()

        # Borrar usuario de Teams
        success = teams_svc.delete_user(upn)

        if success:
            # Marcar como no procesado en Teams
            alumno.teams_procesado = False
            alumno.save(update_fields=['teams_procesado'])

            logger.info(f"[Borrar Teams] ✅ Usuario {upn} eliminado de Teams")
            log_to_db(
                'SUCCESS',
                'tasks_delete',
                f'Usuario eliminado de Teams: {upn}',
                detalles={'upn': upn, 'teams_procesado': False},
                alumno=alumno
            )

            # Actualizar tarea
            tarea.estado = Tarea.EstadoTarea.COMPLETED
            tarea.hora_fin = timezone.now()
            tarea.detalles['resultado'] = 'exito'
            tarea.save()

            return {'success': True, 'upn': upn, 'message': 'Usuario eliminado de Teams'}
        else:
            logger.error(f"[Borrar Teams] ❌ Error eliminando {upn} de Teams")
            log_to_db(
                'ERROR',
                'tasks_delete',
                f'Error eliminando usuario de Teams: {upn}',
                alumno=alumno
            )

            # Actualizar tarea
            tarea.estado = Tarea.EstadoTarea.FAILED
            tarea.hora_fin = timezone.now()
            tarea.mensaje_error = f'Error eliminando usuario {upn} de Teams'
            tarea.save()

            return {'success': False, 'upn': upn, 'error': 'Error eliminando usuario de Teams'}

    except Alumno.DoesNotExist:
        logger.error(f"[Borrar Teams] Alumno {alumno_id} no encontrado")
        return {'success': False, 'error': f'Alumno {alumno_id} no encontrado'}
    except Exception as e:
        logger.error(f"[Borrar Teams] Error: {e}")
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def eliminar_solo_moodle(self, alumno_id, username):
    """
    Elimina usuario solo de Moodle.

    - Marca moodle_procesado=False
    - NO borra de Teams
    - NO borra de base de datos

    Args:
        alumno_id: ID del alumno
        username: Username del usuario en Moodle (email institucional)
    """
    from .services.moodle_service import MoodleService

    try:
        alumno = Alumno.objects.get(id=alumno_id)
        logger.info(f"[Borrar Moodle] Iniciando borrado de {username} (Alumno ID: {alumno_id})")

        # Crear registro de tarea
        tarea = Tarea.objects.create(
            tipo=Tarea.TipoTarea.ELIMINAR_CUENTA,
            estado=Tarea.EstadoTarea.RUNNING,
            celery_task_id=self.request.id,
            alumno=alumno,
            hora_inicio=timezone.now(),
            detalles={'accion': 'borrar_moodle', 'username': username}
        )

        moodle_svc = MoodleService()

        # Intentar borrar usuario de Moodle
        try:
            success = moodle_svc.delete_user(username, alumno)
        except ValueError as e:
            error_msg = str(e)
            # Ignorar error de "usuario no encontrado" (M-002)
            if 'M-002' in error_msg or 'no encontrado' in error_msg.lower():
                logger.info(f"[Borrar Moodle] ℹ️ Usuario {username} no existe en Moodle (ya estaba borrado)")
                log_to_db(
                    'INFO',
                    'tasks_delete',
                    f'Usuario no encontrado en Moodle (ya borrado): {username}',
                    detalles={'username': username, 'ignorado': True},
                    alumno=alumno
                )

                # Marcar tarea como completada (ya está borrado)
                tarea.estado = Tarea.EstadoTarea.COMPLETED
                tarea.hora_fin = timezone.now()
                tarea.detalles['resultado'] = 'usuario_no_encontrado'
                tarea.save()

                return {'success': True, 'username': username, 'message': 'Usuario no encontrado (ya borrado)'}
            else:
                # Otro error, registrar como fallo
                raise

        if success:
            # Marcar como no procesado en Moodle
            alumno.moodle_procesado = False
            alumno.save(update_fields=['moodle_procesado'])

            logger.info(f"[Borrar Moodle] ✅ Usuario {username} eliminado de Moodle")
            log_to_db(
                'SUCCESS',
                'tasks_delete',
                f'Usuario eliminado de Moodle: {username}',
                detalles={'username': username, 'moodle_procesado': False},
                alumno=alumno
            )

            # Actualizar tarea
            tarea.estado = Tarea.EstadoTarea.COMPLETED
            tarea.hora_fin = timezone.now()
            tarea.detalles['resultado'] = 'exito'
            tarea.save()

            return {'success': True, 'username': username, 'message': 'Usuario eliminado de Moodle'}
        else:
            logger.error(f"[Borrar Moodle] ❌ Error eliminando {username} de Moodle")
            log_to_db(
                'ERROR',
                'tasks_delete',
                f'Error eliminando usuario de Moodle: {username}',
                alumno=alumno
            )

            # Actualizar tarea
            tarea.estado = Tarea.EstadoTarea.FAILED
            tarea.hora_fin = timezone.now()
            tarea.mensaje_error = f'Error eliminando usuario {username} de Moodle'
            tarea.save()

            return {'success': False, 'username': username, 'error': 'Error eliminando usuario de Moodle'}

    except Alumno.DoesNotExist:
        logger.error(f"[Borrar Moodle] Alumno {alumno_id} no encontrado")
        return {'success': False, 'error': f'Alumno {alumno_id} no encontrado'}
    except Exception as e:
        logger.error(f"[Borrar Moodle] Error: {e}")
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def eliminar_alumno_completo(self, alumno_id):
    """
    Elimina alumno completamente: Teams + Moodle + Base de datos.

    Secuencia:
    1. Borrar de Teams (si teams_procesado=True)
    2. Borrar de Moodle (si moodle_procesado=True)
    3. Eliminar de base de datos

    Args:
        alumno_id: ID del alumno
    """
    from .services.teams_service import TeamsService
    from .services.moodle_service import MoodleService

    try:
        alumno = Alumno.objects.get(id=alumno_id)
        logger.info(f"[Eliminar Completo] Iniciando eliminación completa de alumno ID: {alumno_id}")

        # Crear registro de tarea
        tarea = Tarea.objects.create(
            tipo=Tarea.TipoTarea.ELIMINAR_CUENTA,
            estado=Tarea.EstadoTarea.RUNNING,
            celery_task_id=self.request.id,
            alumno=alumno,
            hora_inicio=timezone.now(),
            detalles={'accion': 'eliminar_completo'}
        )

        resultados = {
            'teams': None,
            'moodle': None,
            'database': None
        }

        # 1. Borrar de Teams si está procesado
        if alumno.teams_procesado and alumno.email_institucional:
            logger.info(f"[Eliminar Completo] Borrando de Teams: {alumno.email_institucional}")
            teams_svc = TeamsService()
            teams_success = teams_svc.delete_user(alumno.email_institucional)
            resultados['teams'] = teams_success

            if teams_success:
                logger.info(f"[Eliminar Completo] ✅ Borrado de Teams exitoso")
                log_to_db(
                    'SUCCESS',
                    'tasks_delete',
                    f'Usuario eliminado de Teams: {alumno.email_institucional}',
                    alumno=alumno
                )
            else:
                logger.warning(f"[Eliminar Completo] ⚠️ Error borrando de Teams")
                log_to_db(
                    'WARNING',
                    'tasks_delete',
                    f'Error eliminando de Teams: {alumno.email_institucional}',
                    alumno=alumno
                )
        else:
            logger.info(f"[Eliminar Completo] Alumno no procesado en Teams, omitiendo")
            resultados['teams'] = 'not_processed'

        # 2. Borrar de Moodle si está procesado
        if alumno.moodle_procesado and alumno.email_institucional:
            logger.info(f"[Eliminar Completo] Borrando de Moodle: {alumno.email_institucional}")
            moodle_svc = MoodleService()
            moodle_success = moodle_svc.delete_user(alumno.email_institucional)
            resultados['moodle'] = moodle_success

            if moodle_success:
                logger.info(f"[Eliminar Completo] ✅ Borrado de Moodle exitoso")
                log_to_db(
                    'SUCCESS',
                    'tasks_delete',
                    f'Usuario eliminado de Moodle: {alumno.email_institucional}',
                    alumno=alumno
                )
            else:
                logger.warning(f"[Eliminar Completo] ⚠️ Error borrando de Moodle")
                log_to_db(
                    'WARNING',
                    'tasks_delete',
                    f'Error eliminando de Moodle: {alumno.email_institucional}',
                    alumno=alumno
                )
        else:
            logger.info(f"[Eliminar Completo] Alumno no procesado en Moodle, omitiendo")
            resultados['moodle'] = 'not_processed'

        # 3. Eliminar de base de datos
        alumno_nombre = f"{alumno.apellido}, {alumno.nombre}"
        alumno_dni = alumno.dni
        logger.info(f"[Eliminar Completo] Eliminando de base de datos: {alumno_nombre} (DNI: {alumno_dni})")

        alumno.delete()
        resultados['database'] = True

        logger.info(f"[Eliminar Completo] ✅ Alumno eliminado completamente: {alumno_nombre}")
        log_to_db(
            'SUCCESS',
            'tasks_delete',
            f'Alumno eliminado completamente: {alumno_nombre} (DNI: {alumno_dni})',
            detalles=resultados
        )

        # Actualizar tarea (sin alumno porque ya fue eliminado)
        tarea.estado = Tarea.EstadoTarea.COMPLETED
        tarea.hora_fin = timezone.now()
        tarea.detalles['resultados'] = resultados
        tarea.alumno = None  # Ya no existe
        tarea.save()

        return {
            'success': True,
            'message': f'Alumno {alumno_nombre} eliminado completamente',
            'resultados': resultados
        }

    except Alumno.DoesNotExist:
        logger.error(f"[Eliminar Completo] Alumno {alumno_id} no encontrado")
        return {'success': False, 'error': f'Alumno {alumno_id} no encontrado'}
    except Exception as e:
        logger.error(f"[Eliminar Completo] Error: {e}")

        # Intentar actualizar tarea si existe
        try:
            tarea.estado = Tarea.EstadoTarea.FAILED
            tarea.hora_fin = timezone.now()
            tarea.mensaje_error = str(e)
            tarea.save()
        except:
            pass

        return {'success': False, 'error': str(e)}
