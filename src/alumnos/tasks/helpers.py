"""
Nombre del Módulo: helpers.py

Descripción:
Funciones auxiliares compartidas para activar servicios de alumnos.

Autor: Carlos Dagorret
Fecha de Creación: 2025-12-29
Última Modificación: 2025-12-29

Licencia: MIT
Copyright (c) 2025 Carlos Dagorret
"""

import logging
import time
from celery import shared_task
from django.utils import timezone
from ..models import Configuracion, Log, Tarea, Alumno
from ..services.teams_service import TeamsService
from ..services.email_service import EmailService

logger = logging.getLogger(__name__)


@shared_task
def activar_servicios_alumno(alumno_id):
    """
    Tarea asíncrona para activar servicios según el estado del alumno.

    🔧 LÓGICA POR ESTADO:
    - PREINSCRIPTO: Solo envía email de bienvenida (sin Teams, sin Moodle)
    - ASPIRANTE/INGRESANTE: Crea Teams + envía credenciales + enrolla Moodle

    Si Teams falla, envía email de bienvenida sin credenciales.
    Los errores se registran en logs y en la tabla Log.

    Args:
        alumno_id: ID del alumno
    """
    from .models import Alumno, Log

    try:
        alumno = Alumno.objects.get(id=alumno_id)
    except Alumno.DoesNotExist:
        logger.error(f"Alumno {alumno_id} no encontrado")
        return

    email_svc = EmailService()

    # 🔧 PREINSCRIPTOS: Solo enviar email de bienvenida
    if alumno.estado_actual == 'preinscripto':
        logger.info(f"[Activar Servicios] Alumno {alumno_id} es PREINSCRIPTO - Solo enviando email de bienvenida")

        email_sent = email_svc.send_welcome_email(alumno)

        if email_sent:
            logger.info(f"✅ Email de bienvenida enviado a preinscripto {alumno.email_personal}")
            Log.objects.create(
                tipo=Log.TipoLog.SUCCESS,
                modulo='activar_servicios',
                mensaje=f"Email de bienvenida enviado a preinscripto",
                detalles={'email': alumno.email_personal, 'alumno_id': alumno_id},
                alumno=alumno
            )
            alumno.email_procesado = True
            alumno.save(update_fields=['email_procesado'])
        else:
            logger.error(f"❌ Error enviando email de bienvenida a preinscripto {alumno.email_personal}")
            Log.objects.create(
                tipo=Log.TipoLog.ERROR,
                modulo='activar_servicios',
                mensaje=f"Error enviando email de bienvenida a preinscripto",
                detalles={'email': alumno.email_personal, 'alumno_id': alumno_id},
                alumno=alumno
            )

        return

    # 🔧 ASPIRANTES/INGRESANTES: Activar Teams + Moodle + Email
    logger.info(f"[Activar Servicios] Alumno {alumno_id} es {alumno.estado_actual.upper()} - Activando Teams + Moodle + Email")

    teams_svc = TeamsService()
    from .services.moodle_service import MoodleService
    moodle_svc = MoodleService()

    teams_success = False
    teams_result = None

    # 1. Intentar crear usuario en Teams
    try:
        teams_result = teams_svc.create_user(alumno)

        if teams_result and teams_result.get('created'):
            teams_success = True
            logger.info(f"✅ Usuario Teams creado para alumno {alumno_id}: {teams_result.get('upn')}")
            Log.objects.create(
                tipo=Log.TipoLog.SUCCESS,
                modulo='activar_servicios',
                mensaje=f"Usuario Teams creado exitosamente",
                detalles={'upn': teams_result.get('upn'), 'alumno_id': alumno_id},
                alumno=alumno
            )
        else:
            logger.warning(f"⚠️ Teams no retornó resultado válido para alumno {alumno_id}")
            Log.objects.create(
                tipo=Log.TipoLog.WARNING,
                modulo='activar_servicios',
                mensaje=f"Teams no retornó resultado válido",
                detalles={'teams_result': teams_result, 'alumno_id': alumno_id},
                alumno=alumno
            )
    except Exception as e:
        logger.error(f"❌ Error creando usuario Teams para alumno {alumno_id}: {e}")
        Log.objects.create(
            tipo=Log.TipoLog.ERROR,
            modulo='activar_servicios',
            mensaje=f"Error al crear usuario en Teams",
            detalles={'error': str(e), 'alumno_id': alumno_id},
            alumno=alumno
        )

    # 2. Enviar email (siempre, aunque Teams falle)
    email_sent = False

    if teams_success and teams_result:
        # Enviar email con credenciales
        logger.info(f"📧 Enviando email con credenciales a {alumno.email}")
        email_sent = email_svc.send_credentials_email(alumno, teams_result)

        if email_sent:
            logger.info(f"✅ Email con credenciales enviado a {alumno.email}")
            Log.objects.create(
                tipo=Log.TipoLog.SUCCESS,
                modulo='activar_servicios',
                mensaje=f"Email con credenciales enviado exitosamente",
                detalles={'email': alumno.email, 'alumno_id': alumno_id},
                alumno=alumno
            )
        else:
            logger.error(f"❌ Error enviando email con credenciales a {alumno.email}")
            Log.objects.create(
                tipo=Log.TipoLog.ERROR,
                modulo='activar_servicios',
                mensaje=f"Error al enviar email con credenciales",
                detalles={'email': alumno.email, 'alumno_id': alumno_id},
                alumno=alumno
            )
    else:
        # Teams falló, enviar email de bienvenida sin credenciales
        logger.info(f"📧 Teams falló, enviando email de bienvenida a {alumno.email}")
        email_sent = email_svc.send_welcome_email(alumno)

        if email_sent:
            logger.info(f"✅ Email de bienvenida enviado a {alumno.email}")
            Log.objects.create(
                tipo=Log.TipoLog.INFO,
                modulo='activar_servicios',
                mensaje=f"Email de bienvenida enviado (Teams no disponible)",
                detalles={'email': alumno.email, 'alumno_id': alumno_id},
                alumno=alumno
            )
        else:
            logger.error(f"❌ Error enviando email de bienvenida a {alumno.email}")
            Log.objects.create(
                tipo=Log.TipoLog.ERROR,
                modulo='activar_servicios',
                mensaje=f"Error al enviar email de bienvenida",
                detalles={'email': alumno.email, 'alumno_id': alumno_id},
                alumno=alumno
            )

    # 3. Enrollar en Moodle
    moodle_success = False
    moodle_result = None

    if alumno.moodle_payload:
        courses = alumno.moodle_payload.get('acciones', {}).get('enrolar', {}).get('courses', [])
        if courses:
            logger.info(f"📚 Enrollando en Moodle: {len(courses)} cursos")
            try:
                moodle_result = moodle_svc.enrol_user(alumno, courses)

                if moodle_result.get('success'):
                    moodle_success = True
                    enrolled = moodle_result.get('enrolled_courses', [])
                    failed = moodle_result.get('failed_courses', [])

                    logger.info(f"✅ Moodle: {len(enrolled)} cursos enrollados, {len(failed)} fallidos")
                    Log.objects.create(
                        tipo=Log.TipoLog.SUCCESS,
                        modulo='activar_servicios',
                        mensaje=f"Enrollamiento en Moodle exitoso",
                        detalles={
                            'enrolled_courses': enrolled,
                            'failed_courses': failed,
                            'user_id': moodle_result.get('user_id')
                        },
                        alumno=alumno
                    )
                else:
                    logger.error(f"❌ Error en enrollamiento Moodle: {moodle_result.get('error')}")
                    Log.objects.create(
                        tipo=Log.TipoLog.ERROR,
                        modulo='activar_servicios',
                        mensaje=f"Error en enrollamiento Moodle",
                        detalles={'error': moodle_result.get('error')},
                        alumno=alumno
                    )

            except Exception as e:
                logger.error(f"❌ Excepción en Moodle para alumno {alumno_id}: {e}")
                Log.objects.create(
                    tipo=Log.TipoLog.ERROR,
                    modulo='activar_servicios',
                    mensaje=f"Excepción al enrollar en Moodle",
                    detalles={'error': str(e)},
                    alumno=alumno
                )
        else:
            logger.info(f"ℹ️ No hay cursos para enrollar en Moodle")
    else:
        logger.info(f"ℹ️ No hay moodle_payload configurado")

    # 4. Marcar flags de procesamiento
    if teams_success:
        alumno.teams_procesado = True
    if moodle_success:
        alumno.moodle_procesado = True

    if teams_success or moodle_success:
        alumno.save(update_fields=['teams_procesado', 'moodle_procesado'])
        logger.info(f"✅ Flags actualizados: Teams={alumno.teams_procesado}, Moodle={alumno.moodle_procesado}")

    # 5. Resumen final
    if teams_success and email_sent and moodle_success:
        logger.info(f"🎉 Todos los servicios activados para alumno {alumno_id} (Teams + Email + Moodle)")
    elif teams_success and email_sent:
        logger.info(f"✅ Teams y Email activados (Moodle: {'OK' if moodle_success else 'falló'})")
    elif teams_success and not email_sent:
        logger.warning(f"⚠️ Usuario Teams creado pero email no enviado para alumno {alumno_id}")
    elif not teams_success and email_sent:
        logger.info(f"📬 Email de bienvenida enviado (Teams no disponible) para alumno {alumno_id}")
    else:
        logger.error(f"💥 Falló todo el proceso para alumno {alumno_id}")




@shared_task(bind=True)
def procesar_alumno_nuevo_completo(self, alumno_id, estado):
    """
    Workflow completo para alumno nuevo según su estado:

    PREINSCRIPTO:
        - Solo enviar email de bienvenida (sin Teams, sin Moodle)

    ASPIRANTE:
        1. Crear cuenta en Teams
        2. Asignar licencia
        3. Enviar email con credenciales Teams
        4. Enrolar en Moodle
        5. Enviar email de enrollamiento Moodle

    INGRESANTE:
        1. Crear cuenta en Teams (si no existe)
        2. Enrolar en Moodle
        3. Enviar email de enrollamiento Moodle

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
        teams_svc = TeamsService()
        email_svc = EmailService()
        from .services.moodle_service import MoodleService
        moodle_svc = MoodleService()

        teams_result = None

        # WORKFLOW SEGÚN ESTADO
        if estado == 'preinscripto':
            # PREINSCRIPTOS: Solo email de bienvenida
            logger.info(f"[Workflow-Preinscripto] Enviando email de bienvenida para {alumno}")
            email_sent = email_svc.send_welcome_email(alumno)

            if email_sent:
                resultados['email'] = True
                alumno.email_procesado = True
                alumno.save(update_fields=['email_procesado'])
                logger.info(f"[Workflow-Preinscripto] ✓ Email de bienvenida enviado")
            else:
                resultados['errores'].append("Email: No se pudo enviar")
                logger.warning(f"[Workflow-Preinscripto] ✗ Email no enviado")

        elif estado == 'aspirante':
            # ASPIRANTES: Teams + Email credenciales + Moodle + Email enrollamiento
            # 1. Crear/Buscar usuario en Teams
            logger.info(f"[Workflow-Aspirante] Paso 1/4: Verificando/Creando usuario Teams para {alumno}")
            teams_result = teams_svc.create_user(alumno)

            if teams_result and (teams_result.get('created') or teams_result.get('already_exists')):
                resultados['teams'] = True
                alumno.teams_procesado = True
                alumno.save(update_fields=['teams_procesado'])
                if teams_result.get('created'):
                    logger.info(f"[Workflow-Aspirante] ✓ Teams creado: {teams_result.get('upn')}")
                else:
                    logger.info(f"[Workflow-Aspirante] ✓ Teams ya existe: {teams_result.get('upn')}")
            else:
                error_msg = teams_result.get('error', 'Error desconocido') if teams_result else 'Error desconocido'
                resultados['errores'].append(f"Teams: {error_msg}")
                logger.warning(f"[Workflow-Aspirante] ✗ Teams falló: {error_msg}")
                # Si falla Teams, abortar workflow
                raise Exception(f"No se pudo crear cuenta Teams: {error_msg}")

            # 2. Enviar email con credenciales Teams
            logger.info(f"[Workflow-Aspirante] Paso 2/4: Enviando email con credenciales Teams")
            email_sent = email_svc.send_credentials_email(alumno, teams_result)

            if email_sent:
                resultados['email_credentials'] = True
                alumno.email_procesado = True
                alumno.save(update_fields=['email_procesado'])
                logger.info(f"[Workflow-Aspirante] ✓ Email de credenciales enviado")
            else:
                resultados['errores'].append("Email credenciales: No se pudo enviar")
                logger.warning(f"[Workflow-Aspirante] ✗ Email de credenciales no enviado")

            # 3. Enrolar en Moodle
            logger.info(f"[Workflow-Aspirante] Paso 3/4: Enrolando en Moodle")
            moodle_result = moodle_svc.create_user(alumno)

            if moodle_result:
                user_id = moodle_result.get('id')
                # Enrolar en cursos desde moodle_payload
                courses_enrolled = []
                courses_failed = []

                if alumno.moodle_payload and 'acciones' in alumno.moodle_payload:
                    enrolar_data = alumno.moodle_payload['acciones'].get('enrolar', {})
                    courses = enrolar_data.get('courses', [])

                    for course_shortname in courses:
                        enrolled = moodle_svc.enrol_user_in_course(user_id, course_shortname, alumno)
                        if enrolled:
                            courses_enrolled.append(course_shortname)
                        else:
                            courses_failed.append(course_shortname)

                if courses_enrolled:
                    resultados['moodle'] = True
                    alumno.moodle_procesado = True
                    alumno.save(update_fields=['moodle_procesado'])
                    logger.info(f"[Workflow-Aspirante] ✓ Moodle: usuario creado y enrollado en {len(courses_enrolled)} cursos")
                else:
                    resultados['errores'].append(f"Moodle: Usuario creado pero sin cursos enrollados")
                    logger.warning(f"[Workflow-Aspirante] ⚠️ Usuario Moodle creado pero sin enrollamientos")
            else:
                resultados['errores'].append("Moodle: No se pudo crear usuario")
                logger.warning(f"[Workflow-Aspirante] ✗ Moodle falló")

            # 4. Enviar email de enrollamiento (si Moodle tuvo éxito)
            if resultados.get('moodle'):
                logger.info(f"[Workflow-Aspirante] Paso 4/4: Enviando email de enrollamiento Moodle")
                email_sent = email_svc.send_enrollment_email(alumno, courses_enrolled)
                if email_sent:
                    resultados['email_enrollment'] = True
                    # Solo marcar email_procesado si no se marcó antes (en credenciales)
                    if not alumno.email_procesado:
                        alumno.email_procesado = True
                        alumno.save(update_fields=['email_procesado'])
                    logger.info(f"[Workflow-Aspirante] ✓ Email de enrollamiento Moodle enviado")
                else:
                    resultados['errores'].append("Email enrollamiento: No se pudo enviar")
                    logger.warning(f"[Workflow-Aspirante] ✗ Email de enrollamiento no enviado")

        elif estado in ['ingresante', 'alumno']:
            # INGRESANTES/ALUMNOS: Teams (si no existe) + Moodle + Email enrollamiento
            # 1. Verificar/Crear Teams
            logger.info(f"[Workflow-Ingresante] Paso 1/3: Verificando/Creando usuario Teams")
            if not alumno.teams_procesado:
                teams_result = teams_svc.create_user(alumno)
                if teams_result and (teams_result.get('created') or teams_result.get('already_exists')):
                    resultados['teams'] = True
                    alumno.teams_procesado = True
                    alumno.save(update_fields=['teams_procesado'])
                    if teams_result.get('created'):
                        logger.info(f"[Workflow-Ingresante] ✓ Teams creado")
                    else:
                        logger.info(f"[Workflow-Ingresante] ✓ Teams ya existe")
                else:
                    logger.warning(f"[Workflow-Ingresante] ⚠️ Teams falló")
                    resultados['errores'].append("Teams: Error al verificar/crear usuario")
            else:
                resultados['teams'] = 'skipped'
                logger.info(f"[Workflow-Ingresante] ↷ Teams ya procesado, saltando")

            # 2. Enrolar en Moodle
            logger.info(f"[Workflow-Ingresante] Paso 2/3: Enrolando en Moodle")
            moodle_result = moodle_svc.create_user(alumno)
            courses_enrolled = []

            if moodle_result:
                user_id = moodle_result.get('id')

                if alumno.moodle_payload and 'acciones' in alumno.moodle_payload:
                    enrolar_data = alumno.moodle_payload['acciones'].get('enrolar', {})
                    courses = enrolar_data.get('courses', [])

                    for course_shortname in courses:
                        enrolled = moodle_svc.enrol_user_in_course(user_id, course_shortname, alumno)
                        if enrolled:
                            courses_enrolled.append(course_shortname)

                if courses_enrolled:
                    resultados['moodle'] = True
                    alumno.moodle_procesado = True
                    alumno.save(update_fields=['moodle_procesado'])
                    logger.info(f"[Workflow-Ingresante] ✓ Enrollado en {len(courses_enrolled)} cursos")

            # 3. Email de enrollamiento (si Moodle tuvo éxito)
            if resultados.get('moodle'):
                logger.info(f"[Workflow-Ingresante] Paso 3/3: Enviando email de enrollamiento Moodle")
                email_sent = email_svc.send_enrollment_email(alumno, courses_enrolled)
                if email_sent:
                    resultados['email_enrollment'] = True
                    alumno.email_procesado = True
                    alumno.save(update_fields=['email_procesado'])
                    logger.info(f"[Workflow-Ingresante] ✓ Email de enrollamiento Moodle enviado")
                else:
                    resultados['errores'].append("Email enrollamiento: No se pudo enviar")
                    logger.warning(f"[Workflow-Ingresante] ✗ Email de enrollamiento no enviado")

        # Workflow completado (aunque email haya fallado, Teams está ok)
        tarea.estado = Tarea.EstadoTarea.COMPLETED
        tarea.cantidad_entidades = 1
        tarea.hora_fin = timezone.now()
        tarea.detalles = {
            'estado': estado,
            'workflow': 'completo',
            'resultados': resultados,
            'upn': teams_result.get('upn') if teams_result else None
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

