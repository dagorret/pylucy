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

        # Preparar datos del usuario
        username = alumno.email_institucional or alumno.email_personal
        if not username:
            logger.error(f"Alumno {alumno.id} no tiene email")
            return None

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

        user_data = {
            'users[0][username]': username,
            'users[0][password]': alumno.teams_password or 'ChangeMe123!',
            'users[0][firstname]': alumno.nombre,
            'users[0][lastname]': alumno.apellido,
            'users[0][email]': email_to_use,
            'users[0][auth]': auth_method,
        }

        result = self._call_webservice('core_user_create_users', user_data)

        if 'error' in result:
            error_msg = result['error']
            errorcode = result.get('errorcode', '')

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
            return None

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

        logger.warning(f"Respuesta inesperada al crear usuario Moodle: {result}")
        return None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Busca un usuario en Moodle por username.

        Args:
            username: Username del usuario

        Returns:
            Dict con información del usuario o None si no existe
        """
        params = {
            'criteria[0][key]': 'username',
            'criteria[0][value]': username,
        }

        result = self._call_webservice('core_user_get_users', params)

        if 'error' in result:
            logger.error(f"Error buscando usuario {username}: {result['error']}")
            return None

        if isinstance(result, dict) and 'users' in result and len(result['users']) > 0:
            return result['users'][0]

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

    def enrol_user_in_course(self, user_id: int, course_shortname: str, alumno=None) -> bool:
        """
        Enrolla un usuario en un curso de Moodle.
        Si ya está enrollado, no hace nada y retorna True.

        Args:
            user_id: ID del usuario en Moodle
            course_shortname: Shortname del curso en Moodle
            alumno: Instancia del modelo Alumno (opcional, para logs)

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
            return True  # Ya está enrollado, éxito

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
        username = alumno.email_institucional or alumno.email_personal
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
                return {'success': False, 'error': 'Error al crear usuario'}
            user_id = created_user['id']

        # 2. Enrollar en cursos
        enrolled = []
        failed = []

        for course_shortname in courses:
            if self.enrol_user_in_course(user_id, course_shortname, alumno):
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
