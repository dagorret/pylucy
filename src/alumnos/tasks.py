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
    Usa consulta incremental: solo trae registros modificados desde última ejecución.
    """
    from datetime import timedelta

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

    # ✨ CONSULTA INCREMENTAL: Calcular desde/hasta
    # Formato YYYYMMDDHHMM requerido por API UTI
    desde = None
    hasta = ahora.strftime('%Y%m%d%H%M')

    if config.ultima_ingesta_preinscriptos:
        # Desde 1 segundo después de última ingesta exitosa
        desde = (config.ultima_ingesta_preinscriptos + timedelta(seconds=1)).strftime('%Y%m%d%H%M')
        logger.info(f"[Ingesta Incremental Preinscriptos] Desde: {desde}, Hasta: {hasta}")
    else:
        logger.info("[Ingesta Completa Preinscriptos] Primera ejecución, trayendo lista completa")

    # Crear registro de tarea
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.INGESTA_PREINSCRIPTOS,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        hora_inicio=timezone.now(),
        detalles={'desde': desde, 'hasta': hasta}
    )

    # Ejecutar ingesta
    try:
        logger.info("[Ingesta Auto-Preinscriptos] Iniciando ingesta automática de preinscriptos")
        # Leer configuración de email
        enviar_email = config.preinscriptos_enviar_email
        logger.info(f"[Ingesta Auto-Preinscriptos] Enviar email: {enviar_email}")

        # ✨ Ejecutar con desde/hasta
        created, updated, errors, nuevos_ids = ingerir_desde_sial(
            tipo='preinscriptos',
            desde=desde,
            hasta=hasta,
            retornar_nuevos=True,
            enviar_email=enviar_email
        )

        # 🔧 CATEGORIZACIÓN DE ERRORES
        errores_categorizados = {
            'uti_api': [],
            'datos_invalidos': [],
            'correo': [],
            'guardado': [],
            'otros': []
        }

        for error in errors:
            if 'Error al consultar listas' in error or 'error datospersonales' in error:
                errores_categorizados['uti_api'].append(error)
            elif 'sin nrodoc' in error or 'Registro sin' in error:
                errores_categorizados['datos_invalidos'].append(error)
            elif 'email' in error.lower():
                errores_categorizados['correo'].append(error)
            elif 'error al guardar' in error:
                errores_categorizados['guardado'].append(error)
            else:
                errores_categorizados['otros'].append(error)

        # Actualizar tarea
        tarea.estado = Tarea.EstadoTarea.COMPLETED
        tarea.cantidad_entidades = created + updated
        tarea.hora_fin = timezone.now()
        tarea.detalles = {
            'created': created,
            'updated': updated,
            'total_errors': len(errors),
            'nuevos_procesados': len(nuevos_ids) if nuevos_ids else 0,
            # 🔧 ERRORES CATEGORIZADOS
            'errores_uti_api': errores_categorizados['uti_api'],
            'errores_datos_invalidos': errores_categorizados['datos_invalidos'],
            'errores_correo': errores_categorizados['correo'],
            'errores_guardado': errores_categorizados['guardado'],
            'errores_otros': errores_categorizados['otros'],
        }
        tarea.save()

        # ✨ Actualizar timestamp de última ingesta exitosa (para próxima consulta incremental)
        config.ultima_ingesta_preinscriptos = ahora
        config.save(update_fields=['ultima_ingesta_preinscriptos'])
        logger.info(f"[Ingesta Auto-Preinscriptos] 🕒 Timestamp actualizado: {ahora}")

        Log.objects.create(
            tipo='SUCCESS' if len(errors) == 0 else 'WARNING',
            modulo='tasks',
            mensaje=f'Ingesta automática de preinscriptos: {created} creados, {updated} actualizados, {len(errors)} errores',
            detalles={
                'created': created,
                'updated': updated,
                'errores_categorizados': errores_categorizados
            }
        )

        # 🔧 LOGS MEJORADOS: Fin con detalles de errores categorizados
        logger.info(f"[Ingesta Auto-Preinscriptos] ✅ Finalizada: {created} creados, {updated} actualizados")
        logger.info(f"[Ingesta Auto-Preinscriptos] Errores: {len(errors)} total")
        if errores_categorizados['uti_api']:
            logger.error(f"[Ingesta Auto-Preinscriptos] ❌ Errores UTI/API: {len(errores_categorizados['uti_api'])}")
            for err in errores_categorizados['uti_api'][:3]:
                logger.error(f"  - {err}")
        if errores_categorizados['datos_invalidos']:
            logger.warning(f"[Ingesta Auto-Preinscriptos] ⚠️ Datos inválidos: {len(errores_categorizados['datos_invalidos'])}")
        if errores_categorizados['correo']:
            logger.warning(f"[Ingesta Auto-Preinscriptos] ⚠️ Errores de correo: {len(errores_categorizados['correo'])}")
        if errores_categorizados['guardado']:
            logger.error(f"[Ingesta Auto-Preinscriptos] ❌ Errores de guardado: {len(errores_categorizados['guardado'])}")

        # 🔧 WORKFLOW AUTOMÁTICO DESHABILITADO - Solo crea/actualiza alumnos
        # Los workflows se ejecutan manualmente desde el admin con acciones atómicas
        logger.info(f"[Ingesta Auto-Preinscriptos] ℹ️ Workflow automático deshabilitado. Usar acciones atómicas en el admin.")
        if nuevos_ids and len(nuevos_ids) > 0:
            logger.info(f"[Ingesta Auto-Preinscriptos] ℹ️ {len(nuevos_ids)} alumnos nuevos creados (sin procesar)")

        # # Procesar alumnos nuevos en lotes (Teams + Moodle + Email) - DESHABILITADO
        # if nuevos_ids and len(nuevos_ids) > 0:
        #     batch_size = config.batch_size
        #     logger.info(f"Detectados {len(nuevos_ids)} alumnos nuevos, lanzando workflow en lotes de {batch_size}")
        #
        #     # Dividir en lotes
        #     for i in range(0, len(nuevos_ids), batch_size):
        #         lote = nuevos_ids[i:i + batch_size]
        #         logger.info(f"Lanzando lote {i//batch_size + 1}: {len(lote)} alumnos")
        #         procesar_lote_alumnos_nuevos.delay(lote, 'preinscripto')

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
    from datetime import timedelta

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

    # ✨ CONSULTA INCREMENTAL: Calcular desde/hasta
    # Formato YYYYMMDDHHMM requerido por API UTI
    desde = None
    hasta = ahora.strftime('%Y%m%d%H%M')

    if config.ultima_ingesta_aspirantes:
        # Desde 1 segundo después de última ingesta exitosa
        desde = (config.ultima_ingesta_aspirantes + timedelta(seconds=1)).strftime('%Y%m%d%H%M')
        logger.info(f"[Ingesta Incremental Aspirantes] Desde: {desde}, Hasta: {hasta}")
    else:
        logger.info("[Ingesta Completa Aspirantes] Primera ejecución, trayendo lista completa")

    # Crear registro de tarea
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.INGESTA_ASPIRANTES,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        hora_inicio=timezone.now()
    )

    try:
        logger.info("[Ingesta Auto-Aspirantes] Iniciando ingesta automática de aspirantes")
        # Leer configuración de email
        enviar_email = config.aspirantes_enviar_email
        logger.info(f"[Ingesta Auto-Aspirantes] Enviar email: {enviar_email}")
        created, updated, errors, nuevos_ids = ingerir_desde_sial(
            tipo='aspirantes',
            desde=desde,
            hasta=hasta,
            retornar_nuevos=True,
            enviar_email=enviar_email
        )

        # 🔧 CATEGORIZACIÓN DE ERRORES
        errores_categorizados = {
            'uti_api': [],
            'datos_invalidos': [],
            'correo': [],
            'guardado': [],
            'otros': []
        }

        for error in errors:
            if 'Error al consultar listas' in error or 'error datospersonales' in error:
                errores_categorizados['uti_api'].append(error)
            elif 'sin nrodoc' in error or 'Registro sin' in error:
                errores_categorizados['datos_invalidos'].append(error)
            elif 'email' in error.lower():
                errores_categorizados['correo'].append(error)
            elif 'error al guardar' in error:
                errores_categorizados['guardado'].append(error)
            else:
                errores_categorizados['otros'].append(error)

        # Actualizar tarea
        tarea.estado = Tarea.EstadoTarea.COMPLETED
        tarea.cantidad_entidades = created + updated
        tarea.hora_fin = timezone.now()
        tarea.detalles = {
            'created': created,
            'updated': updated,
            'total_errors': len(errors),
            'nuevos_procesados': len(nuevos_ids) if nuevos_ids else 0,
            # 🔧 ERRORES CATEGORIZADOS
            'errores_uti_api': errores_categorizados['uti_api'],
            'errores_datos_invalidos': errores_categorizados['datos_invalidos'],
            'errores_correo': errores_categorizados['correo'],
            'errores_guardado': errores_categorizados['guardado'],
            'errores_otros': errores_categorizados['otros'],
        }
        tarea.save()

        # ✨ Actualizar timestamp de última ingesta exitosa
        config.ultima_ingesta_aspirantes = ahora
        config.save(update_fields=['ultima_ingesta_aspirantes'])
        logger.info(f"[Ingesta Auto-Aspirantes] 🕒 Timestamp actualizado: {ahora}")

        Log.objects.create(
            tipo='SUCCESS' if len(errors) == 0 else 'WARNING',
            modulo='tasks',
            mensaje=f'Ingesta automática de aspirantes: {created} creados, {updated} actualizados, {len(errors)} errores',
            detalles={
                'created': created,
                'updated': updated,
                'errores_categorizados': errores_categorizados
            }
        )

        # 🔧 LOGS MEJORADOS: Fin con detalles de errores categorizados
        logger.info(f"[Ingesta Auto-Aspirantes] ✅ Finalizada: {created} creados, {updated} actualizados")
        logger.info(f"[Ingesta Auto-Aspirantes] Errores: {len(errors)} total")
        if errores_categorizados['uti_api']:
            logger.error(f"[Ingesta Auto-Aspirantes] ❌ Errores UTI/API: {len(errores_categorizados['uti_api'])}")
            for err in errores_categorizados['uti_api'][:3]:
                logger.error(f"  - {err}")
        if errores_categorizados['datos_invalidos']:
            logger.warning(f"[Ingesta Auto-Aspirantes] ⚠️ Datos inválidos: {len(errores_categorizados['datos_invalidos'])}")
        if errores_categorizados['correo']:
            logger.warning(f"[Ingesta Auto-Aspirantes] ⚠️ Errores de correo: {len(errores_categorizados['correo'])}")
        if errores_categorizados['guardado']:
            logger.error(f"[Ingesta Auto-Aspirantes] ❌ Errores de guardado: {len(errores_categorizados['guardado'])}")

        # 🔧 WORKFLOW AUTOMÁTICO DESHABILITADO - Solo crea/actualiza alumnos
        # Los workflows se ejecutan manualmente desde el admin con acciones atómicas
        logger.info(f"[Ingesta Auto-Aspirantes] ℹ️ Workflow automático deshabilitado. Usar acciones atómicas en el admin.")
        if nuevos_ids and len(nuevos_ids) > 0:
            logger.info(f"[Ingesta Auto-Aspirantes] ℹ️ {len(nuevos_ids)} aspirantes nuevos creados (sin procesar)")

        # # Procesar alumnos nuevos en lotes (Teams + Moodle + Email) - DESHABILITADO
        # if nuevos_ids and len(nuevos_ids) > 0:
        #     batch_size = config.batch_size
        #     logger.info(f"Detectados {len(nuevos_ids)} aspirantes nuevos, lanzando workflow en lotes de {batch_size}")
        #
        #     # Dividir en lotes
        #     for i in range(0, len(nuevos_ids), batch_size):
        #         lote = nuevos_ids[i:i + batch_size]
        #         logger.info(f"Lanzando lote {i//batch_size + 1}: {len(lote)} aspirantes")
        #         procesar_lote_alumnos_nuevos.delay(lote, 'aspirante')

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
    from datetime import timedelta

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

    # ✨ CONSULTA INCREMENTAL: Calcular desde/hasta
    # Formato YYYYMMDDHHMM requerido por API UTI
    desde = None
    hasta = ahora.strftime('%Y%m%d%H%M')

    if config.ultima_ingesta_ingresantes:
        # Desde 1 segundo después de última ingesta exitosa
        desde = (config.ultima_ingesta_ingresantes + timedelta(seconds=1)).strftime('%Y%m%d%H%M')
        logger.info(f"[Ingesta Incremental Ingresantes] Desde: {desde}, Hasta: {hasta}")
    else:
        logger.info("[Ingesta Completa Ingresantes] Primera ejecución, trayendo lista completa")

    # Crear registro de tarea
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.INGESTA_INGRESANTES,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        hora_inicio=timezone.now()
    )

    try:
        logger.info("[Ingesta Auto-Ingresantes] Iniciando ingesta automática de ingresantes")
        # Leer configuración de email
        enviar_email = config.ingresantes_enviar_email
        logger.info(f"[Ingesta Auto-Ingresantes] Enviar email: {enviar_email}")
        created, updated, errors, nuevos_ids = ingerir_desde_sial(
            tipo='ingresantes',
            desde=desde,
            hasta=hasta,
            retornar_nuevos=True,
            enviar_email=enviar_email
        )

        # 🔧 CATEGORIZACIÓN DE ERRORES
        errores_categorizados = {
            'uti_api': [],
            'datos_invalidos': [],
            'correo': [],
            'guardado': [],
            'otros': []
        }

        for error in errors:
            if 'Error al consultar listas' in error or 'error datospersonales' in error:
                errores_categorizados['uti_api'].append(error)
            elif 'sin nrodoc' in error or 'Registro sin' in error:
                errores_categorizados['datos_invalidos'].append(error)
            elif 'email' in error.lower():
                errores_categorizados['correo'].append(error)
            elif 'error al guardar' in error:
                errores_categorizados['guardado'].append(error)
            else:
                errores_categorizados['otros'].append(error)

        # Actualizar tarea
        tarea.estado = Tarea.EstadoTarea.COMPLETED
        tarea.cantidad_entidades = created + updated
        tarea.hora_fin = timezone.now()
        tarea.detalles = {
            'created': created,
            'updated': updated,
            'total_errors': len(errors),
            'nuevos_procesados': len(nuevos_ids) if nuevos_ids else 0,
            # 🔧 ERRORES CATEGORIZADOS
            'errores_uti_api': errores_categorizados['uti_api'],
            'errores_datos_invalidos': errores_categorizados['datos_invalidos'],
            'errores_correo': errores_categorizados['correo'],
            'errores_guardado': errores_categorizados['guardado'],
            'errores_otros': errores_categorizados['otros'],
        }
        tarea.save()

        # ✨ Actualizar timestamp de última ingesta exitosa
        config.ultima_ingesta_ingresantes = ahora
        config.save(update_fields=['ultima_ingesta_ingresantes'])
        logger.info(f"[Ingesta Auto-Ingresantes] 🕒 Timestamp actualizado: {ahora}")

        Log.objects.create(
            tipo='SUCCESS' if len(errors) == 0 else 'WARNING',
            modulo='tasks',
            mensaje=f'Ingesta automática de ingresantes: {created} creados, {updated} actualizados, {len(errors)} errores',
            detalles={
                'created': created,
                'updated': updated,
                'errores_categorizados': errores_categorizados
            }
        )

        # 🔧 LOGS MEJORADOS: Fin con detalles de errores categorizados
        logger.info(f"[Ingesta Auto-Ingresantes] ✅ Finalizada: {created} creados, {updated} actualizados")
        logger.info(f"[Ingesta Auto-Ingresantes] Errores: {len(errors)} total")
        if errores_categorizados['uti_api']:
            logger.error(f"[Ingesta Auto-Ingresantes] ❌ Errores UTI/API: {len(errores_categorizados['uti_api'])}")
            for err in errores_categorizados['uti_api'][:3]:
                logger.error(f"  - {err}")
        if errores_categorizados['datos_invalidos']:
            logger.warning(f"[Ingesta Auto-Ingresantes] ⚠️ Datos inválidos: {len(errores_categorizados['datos_invalidos'])}")
        if errores_categorizados['correo']:
            logger.warning(f"[Ingesta Auto-Ingresantes] ⚠️ Errores de correo: {len(errores_categorizados['correo'])}")
        if errores_categorizados['guardado']:
            logger.error(f"[Ingesta Auto-Ingresantes] ❌ Errores de guardado: {len(errores_categorizados['guardado'])}")

        # 🔧 WORKFLOW AUTOMÁTICO DESHABILITADO - Solo crea/actualiza alumnos
        # Los workflows se ejecutan manualmente desde el admin con acciones atómicas
        logger.info(f"[Ingesta Auto-Ingresantes] ℹ️ Workflow automático deshabilitado. Usar acciones atómicas en el admin.")
        if nuevos_ids and len(nuevos_ids) > 0:
            logger.info(f"[Ingesta Auto-Ingresantes] ℹ️ {len(nuevos_ids)} ingresantes nuevos creados (sin procesar)")

        # # Procesar alumnos nuevos en lotes (Teams + Moodle + Email) - DESHABILITADO
        # if nuevos_ids and len(nuevos_ids) > 0:
        #     batch_size = config.batch_size
        #     logger.info(f"Detectados {len(nuevos_ids)} ingresantes nuevos, lanzando workflow en lotes de {batch_size}")
        #
        #     # Dividir en lotes
        #     for i in range(0, len(nuevos_ids), batch_size):
        #         lote = nuevos_ids[i:i + batch_size]
        #         logger.info(f"Lanzando lote {i//batch_size + 1}: {len(lote)} ingresantes")
        #         procesar_lote_alumnos_nuevos.delay(lote, 'ingresante')

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
    from .services.moodle_service import MoodleService
    from .services.email_service import EmailService

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


@shared_task(bind=True)
def ingesta_manual_task(self, tipo, n=None, seed=None, desde=None, hasta=None, enviar_email=False, usuario=None):
    """
    Tarea asíncrona para ingesta manual desde el admin.

    🔧 REPARACIÓN: Esta tarea permite que la ingesta manual del admin vaya a la cola
    en lugar de ejecutarse síncronamente (que causaba que el botón "piense").

    Args:
        tipo: Tipo de ingesta (preinscriptos, aspirantes, ingresantes)
        n: Cantidad de registros (opcional)
        seed: Semilla para aleatorización (opcional)
        desde: Fecha desde (opcional)
        hasta: Fecha hasta (opcional)
        enviar_email: Si es True, envía emails de bienvenida
        usuario: Usuario que disparó la ingesta

    Returns:
        dict: Resultado de la ingesta con errores categorizados
    """
    # Mapeo de tipos de tarea
    tipo_tarea_map = {
        'preinscriptos': Tarea.TipoTarea.INGESTA_PREINSCRIPTOS,
        'aspirantes': Tarea.TipoTarea.INGESTA_ASPIRANTES,
        'ingresantes': Tarea.TipoTarea.INGESTA_INGRESANTES,
    }

    # Buscar tarea existente o crear una nueva
    tarea = Tarea.objects.filter(celery_task_id=self.request.id).first()
    if not tarea:
        tarea = Tarea.objects.create(
            tipo=tipo_tarea_map.get(tipo, Tarea.TipoTarea.INGESTA_PREINSCRIPTOS),
            estado=Tarea.EstadoTarea.RUNNING,
            celery_task_id=self.request.id,
            hora_inicio=timezone.now(),
            usuario=usuario,
            detalles={
                'tipo': tipo,
                'n': n,
                'seed': seed,
                'desde': desde,
                'hasta': hasta,
                'enviar_email': enviar_email,
                'origen': 'admin_manual'
            }
        )
    else:
        tarea.estado = Tarea.EstadoTarea.RUNNING
        tarea.hora_inicio = timezone.now()
        tarea.save()

    try:
        logger.info(f"[Ingesta Manual] Iniciando ingesta de {tipo} (usuario: {usuario})")
        logger.info(f"[Ingesta Manual] Parámetros: n={n}, seed={seed}, desde={desde}, hasta={hasta}, enviar_email={enviar_email}")

        # Ejecutar ingesta
        created, updated, errors, nuevos_ids = ingerir_desde_sial(
            tipo=tipo,
            n=n,
            fecha=None,
            desde=desde,
            hasta=hasta,
            seed=seed,
            retornar_nuevos=True,
            enviar_email=False  # ❌ NO enviar email síncronamente, se procesa en cola después
        )

        # 🔧 CATEGORIZACIÓN DE ERRORES
        errores_categorizados = {
            'uti_api': [],
            'datos_invalidos': [],
            'correo': [],
            'guardado': [],
            'otros': []
        }

        for error in errors:
            if 'Error al consultar listas' in error or 'error datospersonales' in error:
                errores_categorizados['uti_api'].append(error)
            elif 'sin nrodoc' in error or 'Registro sin' in error:
                errores_categorizados['datos_invalidos'].append(error)
            elif 'email' in error.lower():
                errores_categorizados['correo'].append(error)
            elif 'error al guardar' in error:
                errores_categorizados['guardado'].append(error)
            else:
                errores_categorizados['otros'].append(error)

        # Actualizar tarea con resultados
        tarea.estado = Tarea.EstadoTarea.COMPLETED
        tarea.cantidad_entidades = created + updated
        tarea.hora_fin = timezone.now()
        tarea.detalles = {
            'tipo': tipo,
            'n': n,
            'seed': seed,
            'desde': desde,
            'hasta': hasta,
            'enviar_email': enviar_email,
            'origen': 'admin_manual',
            'created': created,
            'updated': updated,
            'total_errors': len(errors),
            'nuevos_procesados': len(nuevos_ids) if nuevos_ids else 0,
            # 🔧 ERRORES CATEGORIZADOS
            'errores_uti_api': errores_categorizados['uti_api'],
            'errores_datos_invalidos': errores_categorizados['datos_invalidos'],
            'errores_correo': errores_categorizados['correo'],
            'errores_guardado': errores_categorizados['guardado'],
            'errores_otros': errores_categorizados['otros'],
        }
        tarea.save()

        # Log detallado de fin
        logger.info(f"[Ingesta Manual] ✅ Finalizada: {created} creados, {updated} actualizados")
        logger.info(f"[Ingesta Manual] Errores: {len(errors)} total")
        if errores_categorizados['uti_api']:
            logger.error(f"[Ingesta Manual] ❌ Errores UTI/API: {len(errores_categorizados['uti_api'])}")
            for err in errores_categorizados['uti_api'][:3]:  # Primeros 3
                logger.error(f"  - {err}")
        if errores_categorizados['datos_invalidos']:
            logger.warning(f"[Ingesta Manual] ⚠️ Datos inválidos: {len(errores_categorizados['datos_invalidos'])}")
        if errores_categorizados['correo']:
            logger.warning(f"[Ingesta Manual] ⚠️ Errores de correo: {len(errores_categorizados['correo'])}")
        if errores_categorizados['guardado']:
            logger.error(f"[Ingesta Manual] ❌ Errores de guardado: {len(errores_categorizados['guardado'])}")

        Log.objects.create(
            tipo='SUCCESS' if len(errors) == 0 else 'WARNING',
            modulo='tasks',
            mensaje=f'Ingesta manual de {tipo}: {created} creados, {updated} actualizados, {len(errors)} errores',
            detalles={
                'created': created,
                'updated': updated,
                'errores_categorizados': errores_categorizados,
                'usuario': usuario
            }
        )

        # 🔧 WORKFLOW AUTOMÁTICO DESHABILITADO - Solo crea/actualiza alumnos
        # Los workflows se ejecutan manualmente desde el admin con acciones atómicas
        logger.info(f"[Ingesta Manual] ℹ️ Workflow automático deshabilitado. Usar acciones atómicas en el admin.")
        if nuevos_ids and len(nuevos_ids) > 0:
            logger.info(f"[Ingesta Manual] ℹ️ {len(nuevos_ids)} alumnos nuevos creados (sin procesar)")

        # # 🔧 PROCESAR NUEVOS ALUMNOS EN LOTES (Teams + Moodle + Email) - DESHABILITADO
        # if nuevos_ids and len(nuevos_ids) > 0:
        #     config = Configuracion.load()
        #     batch_size = config.batch_size
        #     logger.info(f"[Ingesta Manual] Detectados {len(nuevos_ids)} alumnos nuevos, lanzando workflow en lotes de {batch_size}")
        #
        #     # Determinar estado para workflow
        #     estado_workflow = {
        #         'preinscriptos': 'preinscripto',
        #         'aspirantes': 'aspirante',
        #         'ingresantes': 'ingresante',
        #     }.get(tipo, 'preinscripto')
        #
        #     # Dividir en lotes
        #     for i in range(0, len(nuevos_ids), batch_size):
        #         lote = nuevos_ids[i:i + batch_size]
        #         logger.info(f"[Ingesta Manual] Lanzando lote {i//batch_size + 1}: {len(lote)} alumnos")
        #         procesar_lote_alumnos_nuevos.delay(lote, estado_workflow)

        return {
            'success': True,
            'created': created,
            'updated': updated,
            'errors': len(errors),
            'nuevos': len(nuevos_ids) if nuevos_ids else 0,
            'errores_categorizados': errores_categorizados
        }

    except Exception as e:
        logger.error(f"[Ingesta Manual] ❌ Error fatal en ingesta de {tipo}: {e}")

        tarea.estado = Tarea.EstadoTarea.FAILED
        tarea.mensaje_error = str(e)
        tarea.hora_fin = timezone.now()
        tarea.save()

        Log.objects.create(
            tipo='ERROR',
            modulo='tasks',
            mensaje=f'Error fatal en ingesta manual de {tipo}',
            detalles={'error': str(e), 'usuario': usuario}
        )
        raise


# =============================================================================
# PROCESADOR DE COLA DE TAREAS
# =============================================================================

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
    """Crea usuario en Teams para el alumno asociado a la tarea."""
    if not tarea.alumno:
        return {'success': False, 'error': 'Tarea sin alumno asociado'}

    from .services.teams_service import TeamsService

    teams_service = TeamsService()
    resultado = teams_service.create_user(tarea.alumno)

    # Interpretar resultado de create_user
    # create_user retorna: {'created': True/False, 'already_exists': True, ...} o None
    if resultado and ('created' in resultado or 'already_exists' in resultado):
        # Usuario creado o ya existía → ÉXITO
        # Marcar como procesado en Teams
        tarea.alumno.teams_procesado = True
        tarea.alumno.save(update_fields=['teams_procesado'])

        return {
            'success': True,
            'detalles': {
                'upn': resultado.get('upn'),
                'user_id': resultado.get('id'),
                'created': resultado.get('created', False),
                'already_exists': resultado.get('already_exists', False)
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
    """Enrolla alumno en cursos de Moodle según su estado."""
    if not tarea.alumno:
        return {'success': False, 'error': 'Tarea sin alumno asociado'}

    from .services.moodle_service import MoodleService

    moodle_service = MoodleService()
    resultado = moodle_service.enroll_user_in_courses(tarea.alumno)

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


# =============================================================================
# TAREAS PERSONALIZADAS - Ejemplos
# =============================================================================

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
