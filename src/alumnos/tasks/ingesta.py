"""
Nombre del Módulo: ingesta.py

Descripción:
Tareas de ingesta automática desde SIAL (preinscriptos, aspirantes, ingresantes).

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
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from ..models import Configuracion, Log, Tarea
from ..services import ingerir_desde_sial

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def ingestar_preinscriptos(self):
    """
    Tarea programada para ingestar preinscriptos desde SIAL.
    Usa consulta incremental: solo trae registros modificados desde última ejecución.
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

    # ✨ CONSULTA INCREMENTAL: Calcular desde/hasta
    # Formato YYYYMMDDHHMM requerido por API UTI
    desde = None
    hasta = ahora.strftime('%Y%m%d%H%M')

    # 🔄 VERIFICAR SI SE FUERZA CARGA COMPLETA
    if config.preinscriptos_forzar_carga_completa:
        # FORZAR desde dia_inicio hasta ahora
        if config.preinscriptos_dia_inicio:
            desde = config.preinscriptos_dia_inicio.strftime('%Y%m%d%H%M')
        logger.info(f"[Carga Completa FORZADA Preinscriptos] Desde: {desde or 'inicio'}, Hasta: {hasta}")
        # Desactivar flag después de usarlo
        config.preinscriptos_forzar_carga_completa = False
        config.save(update_fields=['preinscriptos_forzar_carga_completa'])
    elif config.ultima_ingesta_preinscriptos:
        # INCREMENTAL: Desde 1 segundo después de última ingesta exitosa
        desde = (config.ultima_ingesta_preinscriptos + timedelta(seconds=1)).strftime('%Y%m%d%H%M')
        logger.info(f"[Ingesta Incremental Preinscriptos] Desde: {desde}, Hasta: {hasta}")
    else:
        # PRIMERA VEZ: Trayendo lista completa
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
        # Leer configuración de email
        enviar_email = config.preinscriptos_enviar_email

        # ✨ Ejecutar con desde/hasta
        created, updated, errors, nuevos_ids = ingerir_desde_sial(
            tipo='preinscriptos',
            desde=desde,
            hasta=hasta,
            retornar_nuevos=True,
            enviar_email=enviar_email
        )

        # 🔧 DETERMINAR TIPO DE LOG: "Ingesta" si hubo datos, "Chequeo de Ingesta" si no
        total_registros = created + updated
        log_prefix = "Ingesta" if total_registros > 0 else "Chequeo de Ingesta"
        logger.info(f"[{log_prefix} Auto-Preinscriptos] Finalizada: {created} creados, {updated} actualizados")

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
        logger.info(f"[{log_prefix} Auto-Preinscriptos] Timestamp actualizado: {ahora}")

        Log.objects.create(
            tipo='SUCCESS' if len(errors) == 0 else 'WARNING',
            modulo='tasks',
            mensaje=f'{log_prefix} automática de preinscriptos: {created} creados, {updated} actualizados, {len(errors)} errores',
            detalles={
                'created': created,
                'updated': updated,
                'errores_categorizados': errores_categorizados
            }
        )

        # 🔧 LOGS MEJORADOS: Fin con detalles de errores categorizados
        if len(errors) > 0:
            logger.info(f"[{log_prefix} Auto-Preinscriptos] Errores: {len(errors)} total")
        if errores_categorizados['uti_api']:
            logger.error(f"[{log_prefix} Auto-Preinscriptos] Errores UTI/API: {len(errores_categorizados['uti_api'])}")
            for err in errores_categorizados['uti_api'][:3]:
                logger.error(f"  - {err}")
        if errores_categorizados['datos_invalidos']:
            logger.warning(f"[{log_prefix} Auto-Preinscriptos] Datos inválidos: {len(errores_categorizados['datos_invalidos'])}")
        if errores_categorizados['correo']:
            logger.warning(f"[{log_prefix} Auto-Preinscriptos] Errores de correo: {len(errores_categorizados['correo'])}")
        if errores_categorizados['guardado']:
            logger.error(f"[{log_prefix} Auto-Preinscriptos] Errores de guardado: {len(errores_categorizados['guardado'])}")

        # 🔧 WORKFLOW AUTOMÁTICO: PREINSCRIPTOS solo reciben email de bienvenida
        # NO se les crea Teams ni Moodle (solo aspirantes e ingresantes)
        if nuevos_ids and len(nuevos_ids) > 0:
            logger.info(f"[{log_prefix} Auto-Preinscriptos] {len(nuevos_ids)} preinscriptos nuevos detectados")
            logger.info(f"[{log_prefix} Auto-Preinscriptos] Los preinscriptos solo reciben email de bienvenida (sin Teams/Moodle)")

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

    # ✨ CONSULTA INCREMENTAL: Calcular desde/hasta
    # Formato YYYYMMDDHHMM requerido por API UTI
    desde = None
    hasta = ahora.strftime('%Y%m%d%H%M')

    # 🔄 VERIFICAR SI SE FUERZA CARGA COMPLETA
    if config.aspirantes_forzar_carga_completa:
        # FORZAR desde dia_inicio hasta ahora
        if config.aspirantes_dia_inicio:
            desde = config.aspirantes_dia_inicio.strftime('%Y%m%d%H%M')
        logger.info(f"[Carga Completa FORZADA Aspirantes] Desde: {desde or 'inicio'}, Hasta: {hasta}")
        # Desactivar flag después de usarlo
        config.aspirantes_forzar_carga_completa = False
        config.save(update_fields=['aspirantes_forzar_carga_completa'])
    elif config.ultima_ingesta_aspirantes:
        # INCREMENTAL: Desde 1 segundo después de última ingesta exitosa
        desde = (config.ultima_ingesta_aspirantes + timedelta(seconds=1)).strftime('%Y%m%d%H%M')
        logger.info(f"[Ingesta Incremental Aspirantes] Desde: {desde}, Hasta: {hasta}")
    else:
        # PRIMERA VEZ: Trayendo lista completa
        logger.info("[Ingesta Completa Aspirantes] Primera ejecución, trayendo lista completa")

    # Crear registro de tarea
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.INGESTA_ASPIRANTES,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        hora_inicio=timezone.now()
    )

    try:
        logger.info("[{log_prefix} Auto-Aspirantes] Iniciando ingesta automática de aspirantes")
        # Leer configuración de email
        enviar_email = config.aspirantes_enviar_email
        logger.info(f"[{{log_prefix}} Auto-Aspirantes] Enviar email: {enviar_email}")

        # ✨ Ejecutar con desde/hasta
        created, updated, errors, nuevos_ids = ingerir_desde_sial(
            tipo='aspirantes',
            desde=desde,
            hasta=hasta,
            retornar_nuevos=True,
            enviar_email=enviar_email
        )

        # 🔧 DETERMINAR TIPO DE LOG: Ingesta si hubo datos, Chequeo de Ingesta si no
        total_registros = created + updated
        log_prefix = "Ingesta" if total_registros > 0 else "Chequeo de Ingesta"
        logger.info(f"[{log_prefix} Auto-Aspirantes] Finalizada: {created} creados, {updated} actualizados")

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
        logger.info(f"[{log_prefix} Auto-Aspirantes] Timestamp actualizado: {ahora}")

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
        logger.info(f"[{log_prefix} Auto-Aspirantes] Finalizada: {created} creados, {updated} actualizados")
        logger.info(f"[{log_prefix} Auto-Aspirantes] Errores: {len(errors)} total")
        if errores_categorizados['uti_api']:
            logger.error(f"[{log_prefix} Auto-Aspirantes] Errores UTI/API: {len(errores_categorizados['uti_api'])}")
            for err in errores_categorizados['uti_api'][:3]:
                logger.error(f"  - {err}")
        if errores_categorizados['datos_invalidos']:
            logger.warning(f"[{log_prefix} Auto-Aspirantes] Datos inválidos: {len(errores_categorizados['datos_invalidos'])}")
        if errores_categorizados['correo']:
            logger.warning(f"[{log_prefix} Auto-Aspirantes] Errores de correo: {len(errores_categorizados['correo'])}")
        if errores_categorizados['guardado']:
            logger.error(f"[{log_prefix} Auto-Aspirantes] Errores de guardado: {len(errores_categorizados['guardado'])}")

        # 🔧 WORKFLOW AUTOMÁTICO: Crear tareas individuales para Teams y Moodle si está habilitado
        if nuevos_ids and len(nuevos_ids) > 0:
            logger.info(f"[{log_prefix} Auto-Aspirantes] {len(nuevos_ids)} aspirantes nuevos detectados")

            # Crear tareas individuales para cada alumno nuevo
            if config.aspirantes_activar_teams:
                logger.info(f"[{log_prefix} Auto-Aspirantes] Creando {len(nuevos_ids)} tareas individuales Teams")
                for alumno_id in nuevos_ids:
                    Tarea.objects.create(
                        tipo=Tarea.TipoTarea.CREAR_USUARIO_TEAMS,
                        estado=Tarea.EstadoTarea.PENDING,
                        alumno_id=alumno_id,
                        detalles={
                            'origen': 'ingesta_automatica_aspirantes',
                            'enviar_email': True  # Enviar email con credenciales
                        }
                    )

            if config.aspirantes_activar_moodle:
                logger.info(f"[{log_prefix} Auto-Aspirantes] Creando {len(nuevos_ids)} tareas individuales Moodle")
                for alumno_id in nuevos_ids:
                    Tarea.objects.create(
                        tipo=Tarea.TipoTarea.MOODLE_ENROLL,
                        estado=Tarea.EstadoTarea.PENDING,
                        alumno_id=alumno_id,
                        detalles={
                            'origen': 'ingesta_automatica_aspirantes',
                            'enviar_email': True  # Enviar email de enrollamiento Moodle
                        }
                    )

            if not config.aspirantes_activar_teams and not config.aspirantes_activar_moodle:
                logger.info(f"[{log_prefix} Auto-Aspirantes] Sin activación automática configurada")

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

    # ✨ CONSULTA INCREMENTAL: Calcular desde/hasta
    # Formato YYYYMMDDHHMM requerido por API UTI
    desde = None
    hasta = ahora.strftime('%Y%m%d%H%M')

    # 🔄 VERIFICAR SI SE FUERZA CARGA COMPLETA
    if config.ingresantes_forzar_carga_completa:
        # FORZAR desde dia_inicio hasta ahora
        if config.ingresantes_dia_inicio:
            desde = config.ingresantes_dia_inicio.strftime('%Y%m%d%H%M')
        logger.info(f"[Carga Completa FORZADA Ingresantes] Desde: {desde or 'inicio'}, Hasta: {hasta}")
        # Desactivar flag después de usarlo
        config.ingresantes_forzar_carga_completa = False
        config.save(update_fields=['ingresantes_forzar_carga_completa'])
    elif config.ultima_ingesta_ingresantes:
        # INCREMENTAL: Desde 1 segundo después de última ingesta exitosa
        desde = (config.ultima_ingesta_ingresantes + timedelta(seconds=1)).strftime('%Y%m%d%H%M')
        logger.info(f"[Ingesta Incremental Ingresantes] Desde: {desde}, Hasta: {hasta}")
    else:
        # PRIMERA VEZ: Trayendo lista completa
        logger.info("[Ingesta Completa Ingresantes] Primera ejecución, trayendo lista completa")

    # Crear registro de tarea
    tarea = Tarea.objects.create(
        tipo=Tarea.TipoTarea.INGESTA_INGRESANTES,
        estado=Tarea.EstadoTarea.RUNNING,
        celery_task_id=self.request.id,
        hora_inicio=timezone.now()
    )

    try:
        logger.info("[{log_prefix} Auto-Ingresantes] Iniciando ingesta automática de ingresantes")
        # Leer configuración de email
        enviar_email = config.ingresantes_enviar_email
        logger.info(f"[{{log_prefix}} Auto-Ingresantes] Enviar email: {enviar_email}")

        # ✨ Ejecutar con desde/hasta
        created, updated, errors, nuevos_ids = ingerir_desde_sial(
            tipo='ingresantes',
            desde=desde,
            hasta=hasta,
            retornar_nuevos=True,
            enviar_email=enviar_email
        )

        # 🔧 DETERMINAR TIPO DE LOG: Ingesta si hubo datos, Chequeo de Ingesta si no
        total_registros = created + updated
        log_prefix = "Ingesta" if total_registros > 0 else "Chequeo de Ingesta"
        logger.info(f"[{log_prefix} Auto-Ingresantes] Finalizada: {created} creados, {updated} actualizados")

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
        logger.info(f"[{log_prefix} Auto-Ingresantes] Timestamp actualizado: {ahora}")

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
        logger.info(f"[{log_prefix} Auto-Ingresantes] Finalizada: {created} creados, {updated} actualizados")
        logger.info(f"[{log_prefix} Auto-Ingresantes] Errores: {len(errors)} total")
        if errores_categorizados['uti_api']:
            logger.error(f"[{log_prefix} Auto-Ingresantes] Errores UTI/API: {len(errores_categorizados['uti_api'])}")
            for err in errores_categorizados['uti_api'][:3]:
                logger.error(f"  - {err}")
        if errores_categorizados['datos_invalidos']:
            logger.warning(f"[{log_prefix} Auto-Ingresantes] Datos inválidos: {len(errores_categorizados['datos_invalidos'])}")
        if errores_categorizados['correo']:
            logger.warning(f"[{log_prefix} Auto-Ingresantes] Errores de correo: {len(errores_categorizados['correo'])}")
        if errores_categorizados['guardado']:
            logger.error(f"[{log_prefix} Auto-Ingresantes] Errores de guardado: {len(errores_categorizados['guardado'])}")

        # 🔧 WORKFLOW AUTOMÁTICO: Crear tareas individuales para Teams y Moodle si está habilitado
        if nuevos_ids and len(nuevos_ids) > 0:
            logger.info(f"[{log_prefix} Auto-Ingresantes] {len(nuevos_ids)} ingresantes nuevos detectados")

            # Crear tareas individuales para cada alumno nuevo
            if config.ingresantes_activar_teams:
                logger.info(f"[{log_prefix} Auto-Ingresantes] Creando {len(nuevos_ids)} tareas individuales Teams")
                for alumno_id in nuevos_ids:
                    Tarea.objects.create(
                        tipo=Tarea.TipoTarea.CREAR_USUARIO_TEAMS,
                        estado=Tarea.EstadoTarea.PENDING,
                        alumno_id=alumno_id,
                        detalles={
                            'origen': 'ingesta_automatica_ingresantes',
                            'enviar_email': True  # Enviar email con credenciales
                        }
                    )

            if config.ingresantes_activar_moodle:
                logger.info(f"[{log_prefix} Auto-Ingresantes] Creando {len(nuevos_ids)} tareas individuales Moodle")
                for alumno_id in nuevos_ids:
                    Tarea.objects.create(
                        tipo=Tarea.TipoTarea.MOODLE_ENROLL,
                        estado=Tarea.EstadoTarea.PENDING,
                        alumno_id=alumno_id,
                        detalles={
                            'origen': 'ingesta_automatica_ingresantes',
                            'enviar_email': True  # Enviar email de enrollamiento Moodle
                        }
                    )

            if not config.ingresantes_activar_teams and not config.ingresantes_activar_moodle:
                logger.info(f"[{log_prefix} Auto-Ingresantes] Sin activación automática configurada")

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


@shared_task(bind=True)
def ingesta_manual_task(self, tipo, n=None, seed=None, desde=None, hasta=None, enviar_email=False, usuario=None):
    """
    Tarea asíncrona para ingesta manual desde el admin.

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
            enviar_email=False  # NO enviar email síncronamente, se procesa en cola después
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
        logger.info(f"[Ingesta Manual] Finalizada: {created} creados, {updated} actualizados")
        logger.info(f"[Ingesta Manual] Errores: {len(errors)} total")
        if errores_categorizados['uti_api']:
            logger.error(f"[Ingesta Manual] Errores UTI/API: {len(errores_categorizados['uti_api'])}")
            for err in errores_categorizados['uti_api'][:3]:  # Primeros 3
                logger.error(f"  - {err}")
        if errores_categorizados['datos_invalidos']:
            logger.warning(f"[Ingesta Manual] Datos inválidos: {len(errores_categorizados['datos_invalidos'])}")
        if errores_categorizados['correo']:
            logger.warning(f"[Ingesta Manual] Errores de correo: {len(errores_categorizados['correo'])}")
        if errores_categorizados['guardado']:
            logger.error(f"[Ingesta Manual] Errores de guardado: {len(errores_categorizados['guardado'])}")

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

        # Workflow automático deshabilitado - Solo crea/actualiza alumnos
        logger.info(f"[Ingesta Manual] Workflow automático deshabilitado. Usar acciones atómicas en el admin.")
        if nuevos_ids and len(nuevos_ids) > 0:
            logger.info(f"[Ingesta Manual] {len(nuevos_ids)} alumnos nuevos creados (sin procesar)")

        return {
            'success': True,
            'created': created,
            'updated': updated,
            'errors': len(errors),
            'nuevos': len(nuevos_ids) if nuevos_ids else 0,
            'errores_categorizados': errores_categorizados
        }

    except Exception as e:
        logger.error(f"[Ingesta Manual] Error fatal en ingesta de {tipo}: {e}")

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
