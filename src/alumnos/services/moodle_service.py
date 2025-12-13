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
        Crea un usuario en Moodle.

        Args:
            alumno: Instancia del modelo Alumno

        Returns:
            Dict con información del usuario creado o None si falla
        """
        from ..utils.config import get_moodle_email_type, get_moodle_auth_method

        # Preparar datos del usuario
        username = alumno.email_institucional or alumno.email_personal
        if not username:
            logger.error(f"Alumno {alumno.id} no tiene email")
            return None

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

    def enrol_user_in_course(self, user_id: int, course_shortname: str, alumno=None) -> bool:
        """
        Enrolla un usuario en un curso de Moodle.

        Args:
            user_id: ID del usuario en Moodle
            course_shortname: Shortname del curso en Moodle
            alumno: Instancia del modelo Alumno (opcional, para logs)

        Returns:
            True si se enrolló exitosamente, False en caso contrario
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

        # Enrollar con rol de estudiante (usar configuración)
        student_roleid = get_moodle_student_roleid()
        params = {
            'enrolments[0][roleid]': student_roleid,
            'enrolments[0][userid]': user_id,
            'enrolments[0][courseid]': course_id,
        }

        result = self._call_webservice('enrol_manual_enrol_users', params)

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

    def delete_user(self, username: str) -> bool:
        """
        Elimina un usuario de Moodle.

        Args:
            username: Username del usuario a eliminar

        Returns:
            True si se eliminó exitosamente, False en caso contrario
        """
        # Primero buscar el usuario
        user = self.get_user_by_username(username)
        if not user:
            logger.warning(f"Usuario {username} no encontrado en Moodle, no se puede eliminar")
            return False

        user_id = user['id']

        # Eliminar usuario
        params = {
            'userids[0]': user_id
        }

        result = self._call_webservice('core_user_delete_users', params)

        if 'error' in result:
            logger.error(f"Error eliminando usuario {username} de Moodle: {result['error']}")
            return False

        logger.info(f"Usuario {username} (ID: {user_id}) eliminado de Moodle")
        return True
