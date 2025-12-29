"""
Nombre del Módulo: moodle.py

Descripción:
Tareas relacionadas con Moodle (enrollar usuarios en cursos).

Autor: Carlos Dagorret
Fecha de Creación: 2025-12-29
Última Modificación: 2025-12-29

Licencia: MIT
Copyright (c) 2025 Carlos Dagorret
"""

import logging
from celery import shared_task
from ..models import Log, Alumno

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def enrollar_moodle_task(self, alumno_id, enviar_email=False):
    """
    Enrolla un alumno en Moodle, opcionalmente enviando email de enrollamiento.

    Args:
        alumno_id: ID del alumno a enrollar
        enviar_email: Si es True, envía email de enrollamiento Moodle después del enrollamiento exitoso

    Email de enrollamiento incluye:
        - URL del Ecosistema Virtual (v.eco.unrc.edu.ar)
        - Credenciales: UPN + contraseña de Teams
        - Lista de cursos enrollados

    Returns:
        dict: Resultado de la operación
    """
    from ..services.moodle_service import MoodleService
    from ..services.email_service import EmailService

    logger.info(f"[Moodle] Iniciando enrollamiento para alumno_id={alumno_id}, enviar_email={enviar_email}")

    try:
        alumno = Alumno.objects.get(id=alumno_id)
    except Alumno.DoesNotExist:
        logger.error(f"[Moodle] Alumno {alumno_id} no encontrado")
        return {'success': False, 'error': 'Alumno no encontrado'}

    # Validar que tenga email institucional
    if not alumno.email_institucional:
        logger.error(f"[Moodle] Alumno {alumno_id} sin email institucional")
        return {'success': False, 'error': 'Email institucional no configurado'}

    # Enrollar en Moodle
    moodle_svc = MoodleService()
    resultado_moodle = {}

    try:
        logger.info(f"[Moodle] Creando usuario en Moodle: {alumno.email_institucional}")
        moodle_result = moodle_svc.create_user(alumno)

        if moodle_result:
            resultado_moodle['success'] = True
            resultado_moodle['moodle_id'] = moodle_result.get('id')
            user_id = moodle_result.get('id')

            # Enrollar en cursos desde moodle_payload
            courses_enrolled = []
            courses_failed = []

            if alumno.moodle_payload and 'acciones' in alumno.moodle_payload:
                enrolar_data = alumno.moodle_payload['acciones'].get('enrolar', {})
                courses = enrolar_data.get('courses', [])

                logger.info(f"[Moodle] Enrollando usuario {user_id} en {len(courses)} cursos")

                for course_shortname in courses:
                    try:
                        enrolled = moodle_svc.enrol_user_in_course(user_id, course_shortname, alumno)
                        if enrolled:
                            courses_enrolled.append(course_shortname)
                        else:
                            courses_failed.append(course_shortname)
                    except Exception as e:
                        logger.error(f"[Moodle] Error enrollando en curso {course_shortname}: {e}")
                        courses_failed.append(course_shortname)

            resultado_moodle['courses_enrolled'] = courses_enrolled
            resultado_moodle['courses_failed'] = courses_failed

            # Marcar como procesado
            alumno.moodle_procesado = True
            alumno.save()

            Log.objects.create(
                tipo='INFO',
                modulo='tasks',
                mensaje=f'Usuario creado y enrollado en Moodle: {alumno.email_institucional}',
                detalles={
                    'alumno_id': alumno_id,
                    'moodle_id': moodle_result.get('id'),
                    'courses_enrolled': courses_enrolled,
                    'courses_failed': courses_failed
                }
            )
        else:
            resultado_moodle['success'] = False
            resultado_moodle['error'] = 'Error creando usuario en Moodle'

    except Exception as e:
        logger.error(f"[Moodle] Error enrollando alumno {alumno_id}: {e}")
        resultado_moodle['success'] = False
        resultado_moodle['error'] = str(e)

        Log.objects.create(
            tipo='ERROR',
            modulo='tasks',
            mensaje=f'Error enrollando en Moodle: {alumno.email_institucional}',
            detalles={'alumno_id': alumno_id, 'error': str(e)}
        )

    # Enviar email de enrollamiento si se solicita y el enrollamiento fue exitoso
    resultado_email = {}
    if enviar_email and resultado_moodle.get('success'):
        try:
            email_svc = EmailService()
            courses_enrolled = resultado_moodle.get('courses_enrolled', [])
            logger.info(f"[Moodle] Enviando email de enrollamiento a: {alumno.email}")

            email_result = email_svc.send_enrollment_email(alumno, courses_enrolled)

            if email_result:
                resultado_email['success'] = True
                Log.objects.create(
                    tipo='INFO',
                    modulo='tasks',
                    mensaje=f'Email de enrollamiento Moodle enviado a: {alumno.email}',
                    detalles={'alumno_id': alumno_id, 'courses': courses_enrolled}
                )
            else:
                resultado_email['success'] = False
                resultado_email['error'] = 'Error enviando email'

        except Exception as e:
            logger.error(f"[Moodle] Error enviando email: {e}")
            resultado_email['success'] = False
            resultado_email['error'] = str(e)

    # Retornar resultado completo
    resultado_final = {
        'success': resultado_moodle.get('success', False),
        'moodle': resultado_moodle
    }

    if enviar_email:
        resultado_final['email'] = resultado_email

    return resultado_final
