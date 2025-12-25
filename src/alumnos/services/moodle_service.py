"""
Servicio para interactuar con Moodle via Web Services API.

Funcionalidades:
- Crear usuarios en Moodle
- Enrollar usuarios en cursos
- Autenticación via OAuth o token
"""
import logging
from typing import Optional, Dict, List
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def log_to_db(tipo, modulo, mensaje, detalles=None, alumno=None):
    """Registra un log en la base de datos."""
    try:
        from ..models import Log
        Log.objects.create(
            tipo=tipo,
            modulo=modulo,
            mensaje=mensaje,
            detalles=detalles,
            alumno=alumno
        )
    except Exception as e:
        logger.error(f"Error guardando log en BD: {e}")


class MoodleService:
    """Cliente para Moodle Web Services API"""

    def __init__(self):
        # Fallback: Configuracion DB → ENV
        from ..models import Configuracion
        config = Configuracion.load()

        self.base_url = (config.moodle_base_url or settings.MOODLE_BASE_URL).rstrip('/')
        self.wstoken = config.moodle_wstoken or settings.MOODLE_WSTOKEN

    def _call_webservice(self, wsfunction: str, params: dict) -> dict:
        """
        Llama a un web service de Moodle.

        Args:
            wsfunction: Nombre de la función (ej: core_user_create_users)
            params: Parámetros de la función

        Returns:
            Respuesta JSON del servicio
        """
        url = f"{self.base_url}/webservice/rest/server.php"

        data = {
            'wstoken': self.wstoken,
            'wsfunction': wsfunction,
            'moodlewsrestformat': 'json',
            **params
        }

        try:
            logger.info(f"Llamando a Moodle: {wsfunction}")
            # Log parámetros enviados (enmascarando password y token)
            debug_data = {k: '***' if any(x in k.lower() for x in ['password', 'token']) else v for k, v in data.items()}
            logger.info(f"Datos enviados: {debug_data}")

            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()

            # Moodle puede retornar null para operaciones exitosas sin respuesta
            if result is None:
                return {}  # Retornar dict vacío en lugar de None

            # Moodle retorna errores como {"exception": "...", "errorcode": "..."}
            if isinstance(result, dict) and 'exception' in result:
                error_msg = result.get('message', result.get('exception', 'Error desconocido'))
                logger.error(f"Error de Moodle en {wsfunction}: {error_msg}")
                return {'error': error_msg, 'errorcode': result.get('errorcode')}

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con Moodle: {e}")
            return {'error': str(e)}

    def create_user(self, alumno) -> Optional[Dict]:
        """
        Busca usuario en Moodle y lo crea solo si no existe.
        Si ya existe, retorna la información del usuario existente.

        Args:
            alumno: Instancia del modelo Alumno

        Returns:
            Dict con información del usuario (created=True si fue creado, False si ya existía)
        """
        from ..utils.config import get_moodle_email_type, get_moodle_auth_method
        from ..models import Configuracion

        config = Configuracion.load()

        # Preparar datos del usuario con manejo de fallback
        username = alumno.email_institucional
        if not username:
            if config.deshabilitar_fallback_email_personal:
                # Fallback deshabilitado, loguear advertencia y rechazar
                error_msg = f"⚠️ FALTA EMAIL INSTITUCIONAL - Alumno {alumno.id} ({alumno.nombre} {alumno.apellido}) no tiene email_institucional y fallback está deshabilitado"
                logger.warning(error_msg)
                log_to_db(
                    'WARNING',
                    'moodle_service',
                    error_msg,
                    detalles={'alumno_id': alumno.id, 'dni': alumno.dni},
                    alumno=alumno
                )
                raise ValueError(f"M-012: Falta email institucional y fallback deshabilitado")
            else:
                # Usar fallback a email personal
                username = alumno.email_personal

        if not username:
            error_msg = f"Alumno {alumno.id} no tiene email"
            logger.error(error_msg)
            raise ValueError(f"M-001: {error_msg}")

        # 1. BUSCAR PRIMERO si el usuario ya existe
        logger.info(f"Buscando usuario existente en Moodle: {username}")
        existing_user = self.get_user_by_username(username)

        if existing_user:
            logger.info(f"Usuario ya existe en Moodle: {username} (ID: {existing_user['id']})")
            log_to_db(
                'INFO',
                'moodle_service',
                f'Usuario ya existe en Moodle: {username}',
                detalles={'user_id': existing_user['id'], 'username': username},
                alumno=alumno
            )
            return {
                'id': existing_user['id'],
                'username': username,
                'created': False,  # No fue creado ahora
                'already_exists': True
            }

        # 2. Si NO existe, crear usuario nuevo
        logger.info(f"Usuario no existe en Moodle, creando: {username}")

        # Determinar qué email usar según configuración
        email_type = get_moodle_email_type()
        email_to_use = alumno.email_institucional if email_type == 'institucional' else alumno.email_personal
        email_to_use = email_to_use or alumno.email_institucional or alumno.email_personal

        # Determinar método de autenticación según configuración
        auth_method = get_moodle_auth_method()

        # Validar campos requeridos
        if not username or not email_to_use:
            raise ValueError("M-004: Username y email son requeridos")
        if not alumno.nombre or not alumno.apellido:
            raise ValueError("M-004: Nombre y apellido son requeridos")

        # Parámetros básicos según documentación Moodle
        user_data = {
            'users[0][username]': username,
            'users[0][firstname]': str(alumno.nombre).strip(),
            'users[0][lastname]': str(alumno.apellido).strip(),
            'users[0][email]': email_to_use,
            'users[0][auth]': auth_method,
            'users[0][lang]': 'es',  # Idioma español
        }

        # Agregar idnumber solo si existe el DNI
        if alumno.dni:
            user_data['users[0][idnumber]'] = str(alumno.dni).strip()

        # Password: requerido por API aunque con oidc no se use para login
        if auth_method == 'manual':
            user_data['users[0][password]'] = alumno.teams_password or 'ChangeMe123!'
        else:
            # Con oidc, Moodle puede exigir password según políticas
            user_data['users[0][password]'] = 'TempPass-2025!'

        # Log datos enviados (sin password)
        logger.info(f"Creando usuario en Moodle con datos: username={username}, firstname={alumno.nombre}, lastname={alumno.apellido}, email={email_to_use}, auth={auth_method}")

        # Log TODOS los parámetros enviados (enmascarando password)
        debug_data = {k: '***' if 'password' in k.lower() else v for k, v in user_data.items()}
        logger.info(f"Parámetros completos enviados a Moodle: {debug_data}")

        result = self._call_webservice('core_user_create_users', user_data)

        if 'error' in result:
            error_msg = result['error']
            errorcode = result.get('errorcode', '')

            # Log completo de la respuesta para debugging
            logger.error(f"Respuesta completa de Moodle: {result}")

            # Si el usuario ya existe, intentar buscarlo
            if 'already exists' in error_msg.lower() or errorcode == 'invalidusername':
                logger.warning(f"Usuario {username} ya existe en Moodle, buscando...")
                existing_user = self.get_user_by_username(username)
                if existing_user:
                    logger.info(f"Usuario encontrado: {username} (ID: {existing_user['id']})")
                    return {
                        'id': existing_user['id'],
                        'username': username,
                        'created': False  # Ya existía
                    }

            logger.error(f"Error creando usuario Moodle para {username}: {error_msg}")
            log_to_db(
                'ERROR',
                'moodle_service',
                f"Error creando usuario en Moodle: {error_msg}",
                detalles={'username': username, 'error': result},
                alumno=alumno
            )
            raise ValueError(f"M-004: Error al crear usuario en Moodle - {error_msg}")

        if isinstance(result, list) and len(result) > 0:
            user_id = result[0].get('id')
            logger.info(f"Usuario Moodle creado: {username} (ID: {user_id})")
            log_to_db(
                'SUCCESS',
                'moodle_service',
                f"Usuario Moodle creado exitosamente: {username}",
                detalles={'user_id': user_id, 'username': username},
                alumno=alumno
            )
            return {
                'id': user_id,
                'username': username,
                'created': True
            }

        error_msg = f"Respuesta inesperada al crear usuario Moodle: {result}"
        logger.error(error_msg)
        log_to_db(
            'ERROR',
            'moodle_service',
            error_msg,
            detalles={'username': username, 'result': result},
            alumno=alumno
        )
        raise ValueError(f"M-004: {error_msg}")

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Busca un usuario en Moodle por username usando core_user_get_users_by_field.

        Args:
            username: Username del usuario

        Returns:
            Dict con información del usuario o None si no existe
        """
        params = {
            'field': 'username',
            'values[0]': username,
        }

        result = self._call_webservice('core_user_get_users_by_field', params)

        if 'error' in result:
            logger.error(f"Error buscando usuario {username}: {result['error']}")
            return None

        # core_user_get_users_by_field retorna array directamente
        if isinstance(result, list) and len(result) > 0:
            return result[0]

        return None

    def is_user_enrolled_in_course(self, user_id: int, course_id: int) -> bool:
        """
        Verifica si un usuario ya está enrollado en un curso.

        Args:
            user_id: ID del usuario en Moodle
            course_id: ID del curso en Moodle

        Returns:
            True si ya está enrollado, False en caso contrario
        """
        params = {
            'courseid': course_id,
        }

        result = self._call_webservice('core_enrol_get_enrolled_users', params)

        if 'error' in result or not isinstance(result, list):
            return False

        # Buscar si el user_id está en la lista de enrollados
        for enrolled_user in result:
            if enrolled_user.get('id') == user_id:
                return True

        return False

    def enrol_user_in_course(self, user_id: int, course_shortname: str, alumno=None,
                            modalidad: str = None, comision: str = None) -> bool:
        """
        Enrolla un usuario en un curso de Moodle.
        Si ya está enrollado, no hace nada y retorna True.
        Opcionalmente asigna al usuario a un grupo según modalidad y comisión.

        Args:
            user_id: ID del usuario en Moodle
            course_shortname: Shortname del curso en Moodle
            alumno: Instancia del modelo Alumno (opcional, para logs)
            modalidad: Modalidad del alumno ("1" presencial, "2" distancia) - para grupos
            comision: Comisión del alumno (ej: "COMISION 1", "COMISION 01") - para grupos

        Returns:
            True si se enrolló exitosamente o ya estaba enrollado, False en caso contrario
        """
        from ..utils.config import get_moodle_student_roleid

        # Primero obtener el course_id del shortname
        course = self.get_course_by_shortname(course_shortname)
        if not course:
            logger.error(f"Curso no encontrado en Moodle: {course_shortname}")
            log_to_db(
                'ERROR',
                'moodle_service',
                f"Curso no encontrado en Moodle: {course_shortname}",
                detalles={'shortname': course_shortname},
                alumno=alumno
            )
            return False

        course_id = course['id']
        was_already_enrolled = False

        # Verificar si ya está enrollado
        if self.is_user_enrolled_in_course(user_id, course_id):
            logger.info(f"Usuario {user_id} ya está enrollado en {course_shortname}")
            log_to_db(
                'INFO',
                'moodle_service',
                f"Usuario ya enrollado en curso {course_shortname}",
                detalles={'user_id': user_id, 'course_id': course_id, 'shortname': course_shortname},
                alumno=alumno
            )
            was_already_enrolled = True
        else:
            # Si no está enrollado, enrollar ahora
            logger.info(f"Enrollando usuario {user_id} en curso {course_shortname}")
            student_roleid = get_moodle_student_roleid()
            params = {
                'enrolments[0][roleid]': student_roleid,
                'enrolments[0][userid]': user_id,
                'enrolments[0][courseid]': course_id,
            }

            result = self._call_webservice('enrol_manual_enrol_users', params)

            if result is None:
                logger.error(f"Error enrollando usuario {user_id} en curso {course_shortname}: No response from Moodle")
                log_to_db(
                    'ERROR',
                    'moodle_service',
                    f"Error enrollando en curso {course_shortname}: No response from Moodle",
                    detalles={'user_id': user_id, 'course_id': course_id},
                    alumno=alumno
                )
                return False

            if 'error' in result:
                logger.error(f"Error enrollando usuario {user_id} en curso {course_shortname}: {result['error']}")
                log_to_db(
                    'ERROR',
                    'moodle_service',
                    f"Error enrollando en curso {course_shortname}",
                    detalles={'user_id': user_id, 'course_id': course_id, 'error': result},
                    alumno=alumno
                )
                return False

            # Si no hay error, el enrollamiento fue exitoso
            logger.info(f"Usuario {user_id} enrollado en curso {course_shortname} (ID: {course_id})")
            log_to_db(
                'SUCCESS',
                'moodle_service',
                f"Usuario enrollado exitosamente en {course_shortname}",
                detalles={'user_id': user_id, 'course_id': course_id, 'shortname': course_shortname},
                alumno=alumno
            )

        # Asignar a grupo si se proporcionaron modalidad y comisión
        if modalidad and comision:
            group_name = self.generate_group_name(modalidad, comision)
            logger.info(f"Asignando usuario {user_id} al grupo '{group_name}' en curso {course_shortname}")

            try:
                group_id = self.get_or_create_group(course_id, group_name)
                if group_id:
                    self.add_user_to_group(user_id, group_id, alumno)
                    logger.info(f"Usuario {user_id} agregado al grupo '{group_name}'")
                else:
                    logger.warning(f"No se pudo crear/obtener grupo '{group_name}' en curso {course_shortname}")
            except Exception as e:
                # No fallar todo el enrollamiento si falla la asignación al grupo
                logger.warning(f"Error asignando al grupo '{group_name}': {e}")

        return True

    def get_course_by_shortname(self, shortname: str) -> Optional[Dict]:
        """
        Busca un curso en Moodle por shortname.

        Args:
            shortname: Shortname del curso

        Returns:
            Dict con información del curso o None si no existe
        """
        params = {
            'field': 'shortname',
            'value': shortname,
        }

        result = self._call_webservice('core_course_get_courses_by_field', params)

        if 'error' in result:
            logger.error(f"Error buscando curso {shortname}: {result['error']}")
            return None

        if isinstance(result, dict) and 'courses' in result and len(result['courses']) > 0:
            return result['courses'][0]

        logger.warning(f"Curso no encontrado en Moodle: {shortname}")
        return None

    def enrol_user(self, alumno, courses: List[str]) -> Dict:
        """
        Crea usuario en Moodle (si no existe) y lo enrolla en los cursos especificados.

        Args:
            alumno: Instancia del modelo Alumno
            courses: Lista de shortnames de cursos

        Returns:
            Dict con resultados: {success: bool, user_id: int, enrolled_courses: [...], failed_courses: [...]}
        """
        from ..models import Configuracion

        config = Configuracion.load()

        # Preparar username con manejo de fallback
        username = alumno.email_institucional
        if not username:
            if config.deshabilitar_fallback_email_personal:
                # Fallback deshabilitado, loguear advertencia y rechazar
                error_msg = f"⚠️ FALTA EMAIL INSTITUCIONAL - Alumno {alumno.id} ({alumno.nombre} {alumno.apellido}) no tiene email_institucional y fallback está deshabilitado"
                logger.warning(error_msg)
                log_to_db(
                    'WARNING',
                    'moodle_service',
                    error_msg,
                    detalles={'alumno_id': alumno.id, 'dni': alumno.dni},
                    alumno=alumno
                )
                return {'success': False, 'error': 'M-012: Falta email institucional y fallback deshabilitado'}
            else:
                # Usar fallback a email personal
                username = alumno.email_personal

        if not username:
            logger.error(f"Alumno {alumno.id} no tiene email")
            return {'success': False, 'error': 'No email'}

        # 1. Buscar o crear usuario
        user = self.get_user_by_username(username)
        if user:
            logger.info(f"Usuario ya existe en Moodle: {username} (ID: {user['id']})")
            user_id = user['id']
        else:
            logger.info(f"Creando usuario en Moodle: {username}")
            created_user = self.create_user(alumno)
            if not created_user:
                error_msg = f"Error al crear usuario {username} en Moodle"
                logger.error(error_msg)
                raise ValueError(f"M-004: {error_msg}")
            user_id = created_user['id']

        # 2. Obtener modalidad y comisión del alumno para asignación a grupos
        modalidad = None
        comision = None
        if alumno.carreras_data and isinstance(alumno.carreras_data, list) and len(alumno.carreras_data) > 0:
            carrera_data = alumno.carreras_data[0]
            modalidad = carrera_data.get('modalidad', '').strip()
            comisiones = carrera_data.get('comisiones', [])
            if comisiones and len(comisiones) > 0:
                comision = comisiones[0].get('nombre_comision', '')

        # 3. Enrollar en cursos (con asignación a grupo)
        enrolled = []
        failed = []

        for course_shortname in courses:
            if self.enrol_user_in_course(user_id, course_shortname, alumno, modalidad, comision):
                enrolled.append(course_shortname)
            else:
                failed.append(course_shortname)

        success = len(enrolled) > 0
        return {
            'success': success,
            'user_id': user_id,
            'username': username,
            'enrolled_courses': enrolled,
            'failed_courses': failed,
        }

    def enroll_user_in_courses(self, alumno) -> dict:
        """
        Enrolla un alumno en los cursos que le corresponden según su carrera, modalidad y comisión.
        Filtra cursos desde la tabla cursos_cursoingreso según carreras_data del alumno.

        Args:
            alumno: Instancia del modelo Alumno

        Returns:
            Dict con resultado del enrollamiento
        """
        from django.db import connection

        # Verificar que el alumno tenga carreras_data
        if not alumno.carreras_data or not isinstance(alumno.carreras_data, list):
            logger.warning(f"Alumno {alumno.id} no tiene carreras_data")
            return {
                'success': False,
                'error': 'Alumno no tiene información de carrera/modalidad/comisión'
            }

        # Extraer datos del alumno (tomamos la primera carrera)
        carrera_data = alumno.carreras_data[0]
        nombre_carrera = carrera_data.get('nombre_carrera', '')
        modalidad_codigo = carrera_data.get('modalidad', '')
        comisiones_alumno = [c.get('nombre_comision', '') for c in carrera_data.get('comisiones', [])]

        # Mapeo de nombre de carrera a código
        carrera_map = {
            'CONTADOR PÚBLICO': 'CP',
            'LICENCIATURA EN ECONOMÍA': 'LE',
            'LICENCIATURA EN ADMINISTRACIÓN': 'LA',
            'TECNICATURA EN GESTIÓN ADMINISTRATIVA Y CONTABLE': 'TGA',
            'TECNICATURA EN GESTIÓN DE EMPRESAS': 'TGE',
        }
        codigo_carrera = carrera_map.get(nombre_carrera.upper(), None)

        # Mapeo de modalidad
        modalidad_map = {'1': 'PRES', '2': 'DIST'}
        modalidad = modalidad_map.get(modalidad_codigo, 'PRES')

        if not codigo_carrera:
            logger.error(f"No se pudo mapear carrera: {nombre_carrera}")
            return {
                'success': False,
                'error': f'Carrera no reconocida: {nombre_carrera}'
            }

        logger.info(f"Filtrando cursos para: Carrera={codigo_carrera}, Modalidad={modalidad}, Comisiones={comisiones_alumno}")

        # Consultar todos los cursos activos y filtrar en Python
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT curso_moodle, carreras, modalidades, comisiones
                FROM cursos_cursoingreso
                WHERE activo = true
                ORDER BY curso_moodle
            """)
            all_courses = cursor.fetchall()

        # Filtrar cursos que correspondan al alumno
        import json
        cursos_filtrados = []
        for curso_moodle, carreras_json, modalidades_json, comisiones_json in all_courses:
            carreras = json.loads(carreras_json) if isinstance(carreras_json, str) else carreras_json
            modalidades = json.loads(modalidades_json) if isinstance(modalidades_json, str) else modalidades_json
            comisiones = json.loads(comisiones_json) if isinstance(comisiones_json, str) else comisiones_json

            # Verificar si la carrera del alumno está en el curso
            if codigo_carrera not in carreras:
                continue

            # Verificar si la modalidad del alumno está en el curso
            if modalidad not in modalidades:
                continue

            # Verificar si alguna comisión del alumno está en el curso (o si el curso acepta todas las comisiones)
            comisiones_match = any(com in comisiones for com in comisiones_alumno)
            todas_comisiones = len(comisiones) > 6  # Si tiene muchas comisiones, probablemente acepta todas

            if comisiones_match or todas_comisiones:
                cursos_filtrados.append(curso_moodle)

        if not cursos_filtrados:
            logger.warning(f"No se encontraron cursos para {codigo_carrera}/{modalidad}/{comisiones_alumno}")
            return {
                'success': False,
                'error': 'No hay cursos que correspondan a la carrera/modalidad/comisión del alumno'
            }

        logger.info(f"Cursos filtrados para enrollment: {cursos_filtrados}")

        # Enrollar en los cursos filtrados
        result = self.enrol_user(alumno, cursos_filtrados)
        return result

    def unenrol_user_from_course(self, user_id: int, course_shortname: str, alumno=None) -> bool:
        """
        Des-enrolla un usuario de un curso de Moodle.

        Args:
            user_id: ID del usuario en Moodle
            course_shortname: Shortname del curso en Moodle
            alumno: Instancia del modelo Alumno (opcional, para logs)

        Returns:
            True si se des-enrolló exitosamente o no estaba enrollado, False en caso contrario
        """
        # Primero obtener el course_id del shortname
        course = self.get_course_by_shortname(course_shortname)
        if not course:
            logger.error(f"Curso no encontrado en Moodle: {course_shortname}")
            log_to_db(
                'ERROR',
                'moodle_service',
                f"Curso no encontrado en Moodle: {course_shortname}",
                detalles={'shortname': course_shortname},
                alumno=alumno
            )
            raise ValueError(f"M-005: Curso no encontrado - {course_shortname}")

        course_id = course['id']

        # Verificar si está enrollado
        if not self.is_user_enrolled_in_course(user_id, course_id):
            logger.info(f"Usuario {user_id} no está enrollado en {course_shortname}")
            log_to_db(
                'INFO',
                'moodle_service',
                f"Usuario no estaba enrollado en curso {course_shortname}",
                detalles={'user_id': user_id, 'course_id': course_id, 'shortname': course_shortname},
                alumno=alumno
            )
            return True  # No estaba enrollado, éxito

        # Si está enrollado, des-enrollar ahora
        logger.info(f"Des-enrollando usuario {user_id} de curso {course_shortname}")
        params = {
            'enrolments[0][userid]': user_id,
            'enrolments[0][courseid]': course_id,
        }

        result = self._call_webservice('enrol_manual_unenrol_users', params)

        if result is None:
            logger.error(f"Error des-enrollando usuario {user_id} del curso {course_shortname}: No response from Moodle")
            log_to_db(
                'ERROR',
                'moodle_service',
                f"Error des-enrollando de curso {course_shortname}: No response from Moodle",
                detalles={'user_id': user_id, 'course_id': course_id},
                alumno=alumno
            )
            raise ValueError(f"M-010: Error de conexión con Moodle")

        if 'error' in result:
            logger.error(f"Error des-enrollando usuario {user_id} del curso {course_shortname}: {result['error']}")
            log_to_db(
                'ERROR',
                'moodle_service',
                f"Error des-enrollando de curso {course_shortname}",
                detalles={'user_id': user_id, 'course_id': course_id, 'error': result},
                alumno=alumno
            )
            raise ValueError(f"M-006: Error al des-enrollar del curso - {result['error']}")

        # Verificar que realmente se des-enrolló
        import time
        time.sleep(0.5)  # Esperar medio segundo para que Moodle procese

        still_enrolled = self.is_user_enrolled_in_course(user_id, course_id)
        if still_enrolled:
            logger.error(f"Usuario {user_id} sigue enrollado en {course_shortname} después de llamar a unenrol")
            log_to_db(
                'ERROR',
                'moodle_service',
                f"Des-enrollamiento falló: usuario sigue enrollado en {course_shortname}",
                detalles={'user_id': user_id, 'course_id': course_id, 'shortname': course_shortname},
                alumno=alumno
            )
            raise ValueError(f"M-011: Des-enrollamiento falló - usuario sigue enrollado")

        # Si no hay error, el des-enrollamiento fue exitoso
        logger.info(f"Usuario {user_id} des-enrollado del curso {course_shortname} (ID: {course_id})")
        log_to_db(
            'SUCCESS',
            'moodle_service',
            f"Usuario des-enrollado exitosamente de {course_shortname}",
            detalles={'user_id': user_id, 'course_id': course_id, 'shortname': course_shortname},
            alumno=alumno
        )
        return True

    def delete_user(self, username: str, alumno=None) -> bool:
        """
        Elimina un usuario de Moodle.

        Args:
            username: Username del usuario a eliminar
            alumno: Instancia del modelo Alumno (opcional, para logging)

        Returns:
            True si se eliminó exitosamente, False en caso contrario
        """
        # Primero buscar el usuario
        user = self.get_user_by_username(username)
        if not user:
            logger.warning(f"Usuario {username} no encontrado en Moodle, no se puede eliminar")
            log_to_db('WARNING', 'moodle_service', f'Usuario no encontrado: {username}', alumno=alumno)
            raise ValueError(f"M-007: Usuario ya enrollado en curso")  # Reutilizando código existente

        user_id = user['id']

        # Eliminar usuario
        params = {
            'userids[0]': user_id
        }

        result = self._call_webservice('core_user_delete_users', params)

        if 'error' in result:
            logger.error(f"Error eliminando usuario {username} de Moodle: {result['error']}")
            log_to_db('ERROR', 'moodle_service', f'Error eliminando usuario {username}',
                     detalles={'error': result}, alumno=alumno)
            raise ValueError(f"M-004: Error al eliminar usuario en Moodle - {result['error']}")

        logger.info(f"Usuario {username} (ID: {user_id}) eliminado de Moodle")
        log_to_db('SUCCESS', 'moodle_service', f'Usuario eliminado exitosamente: {username}', alumno=alumno)
        return True

    def get_course_groups(self, course_id: int) -> List[Dict]:
        """
        Obtiene todos los grupos de un curso.

        Args:
            course_id: ID del curso en Moodle

        Returns:
            Lista de grupos [{'id': 123, 'name': 'P1', 'courseid': 456}, ...]
        """
        params = {'courseid': course_id}
        result = self._call_webservice('core_group_get_course_groups', params)

        if 'error' in result:
            logger.error(f"Error obteniendo grupos del curso {course_id}: {result['error']}")
            return []

        return result if isinstance(result, list) else []

    def create_group(self, course_id: int, group_name: str, description: str = "") -> Optional[int]:
        """
        Crea un grupo en un curso.

        Args:
            course_id: ID del curso en Moodle
            group_name: Nombre del grupo (ej: "P1", "D2")
            description: Descripción del grupo (opcional)

        Returns:
            ID del grupo creado o None si falló
        """
        params = {
            'groups[0][courseid]': course_id,
            'groups[0][name]': group_name,
            'groups[0][description]': description,
        }

        result = self._call_webservice('core_group_create_groups', params)

        if 'error' in result:
            logger.error(f"Error creando grupo '{group_name}' en curso {course_id}: {result['error']}")
            return None

        if isinstance(result, list) and len(result) > 0:
            group_id = result[0].get('id')
            logger.info(f"Grupo creado: '{group_name}' (ID: {group_id})")
            return group_id

        return None

    def add_user_to_group(self, user_id: int, group_id: int, alumno=None) -> bool:
        """
        Agrega un usuario a un grupo.

        Args:
            user_id: ID del usuario en Moodle
            group_id: ID del grupo en Moodle
            alumno: Instancia del modelo Alumno (opcional, para logs)

        Returns:
            True si se agregó exitosamente, False en caso contrario
        """
        params = {
            'members[0][groupid]': group_id,
            'members[0][userid]': user_id,
        }

        result = self._call_webservice('core_group_add_group_members', params)

        # La API retorna None en éxito
        if result is None or (isinstance(result, dict) and not result.get('error')):
            logger.info(f"Usuario {user_id} agregado al grupo {group_id}")
            log_to_db(
                'SUCCESS',
                'moodle_service',
                f"Usuario agregado al grupo {group_id}",
                detalles={'user_id': user_id, 'group_id': group_id},
                alumno=alumno
            )
            return True

        if 'error' in result:
            logger.error(f"Error agregando usuario {user_id} al grupo {group_id}: {result['error']}")
            log_to_db(
                'ERROR',
                'moodle_service',
                f"Error agregando al grupo {group_id}",
                detalles={'user_id': user_id, 'group_id': group_id, 'error': result},
                alumno=alumno
            )
            return False

        return False

    def get_or_create_group(self, course_id: int, group_name: str) -> Optional[int]:
        """
        Busca un grupo por nombre, lo crea si no existe.

        Args:
            course_id: ID del curso en Moodle
            group_name: Nombre del grupo (ej: "P1", "D2")

        Returns:
            ID del grupo
        """
        # Buscar grupo existente
        groups = self.get_course_groups(course_id)
        for group in groups:
            if group.get('name') == group_name:
                logger.info(f"Grupo '{group_name}' ya existe (ID: {group['id']})")
                return group['id']

        # Si no existe, crear
        logger.info(f"Grupo '{group_name}' no existe, creando...")
        return self.create_group(course_id, group_name)

    def generate_group_name(self, modalidad: str, comision: str) -> str:
        """
        Genera el nombre del grupo según modalidad y comisión.

        Lógica:
        - Presencial (1) + COMISION 2 → "P2"
        - Distancia (2) + COMISION 01 → "D1"

        Args:
            modalidad: "1" (presencial) o "2" (distancia)
            comision: Nombre de la comisión (ej: "COMISION 1", "COMISION 01")

        Returns:
            Nombre del grupo (ej: "P1", "D2")
        """
        import re

        # Determinar prefijo
        prefix = "P" if modalidad == "1" else "D"

        # Extraer número de la comisión (quitando ceros al inicio)
        if comision:
            # Buscar patrón "COMISION X" o solo el número
            match = re.search(r'COMISI[OÓ]N\s+(\d+)', comision, re.IGNORECASE)
            if match:
                num = match.group(1).lstrip('0') or '0'  # Quitar ceros, si queda vacío usar '0'
            else:
                # Si solo viene el número
                num = str(comision).lstrip('0') or '0'
        else:
            num = '0'

        group_name = f"{prefix}{num}"
        logger.info(f"Grupo generado: modalidad={modalidad}, comision={comision} → {group_name}")
        return group_name

    def get_required_groups_for_courses(self, course_shortnames: List[str] = None) -> Dict[str, List[str]]:
        """
        Genera la lista de grupos que deberían existir en cada curso.

        Args:
            course_shortnames: Lista de shortnames de cursos (opcional, si no se provee usa todos los activos)

        Returns:
            Dict con {course_shortname: [grupos_necesarios]}
            Ejemplo: {'I3': ['P1', 'P2', 'P3', 'D1', 'D2', 'D3'], ...}
        """
        # Grupos estándar: Presencial 1-5 y Distancia 1-5
        grupos_estandar = []
        for i in range(1, 6):
            grupos_estandar.append(f'P{i}')  # Presencial 1-5
            grupos_estandar.append(f'D{i}')  # Distancia 1-5

        if course_shortnames is None:
            # Si no se especifican cursos, usar todos los cursos activos
            from cursos.models import CursoIngreso
            course_shortnames = list(
                CursoIngreso.objects.filter(activo=True)
                .values_list('curso_moodle', flat=True)
                .distinct()
            )

        result = {}
        for shortname in course_shortnames:
            result[shortname] = grupos_estandar.copy()

        logger.info(f"Grupos necesarios generados para {len(result)} cursos")
        return result
