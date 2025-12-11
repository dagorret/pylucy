"""
Servicio de integración con Microsoft Teams/Azure AD usando Graph API.

Funcionalidades:
- Crear usuarios en Azure AD
- Asignar licencias Microsoft 365 A1 automáticamente
- Obtener información de usuarios
- Gestionar contraseñas
"""
import requests
import logging
from typing import Optional, Dict, List
from django.conf import settings

logger = logging.getLogger(__name__)


def log_to_db(tipo, modulo, mensaje, detalles=None, alumno=None):
    """
    Registra un log en la base de datos.
    Se importa aquí para evitar problemas de importación circular.
    """
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


class TeamsService:
    """Cliente para Microsoft Graph API - Gestión de usuarios Teams/Azure AD"""

    BASE_URL = "https://graph.microsoft.com/v1.0"
    TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    # SKU ID para Microsoft 365 A1 para estudiantes
    # Nota: Este ID puede variar, lo verificaremos en la primera ejecución
    STUDENT_SKU_PART_NUMBER = "STANDARDWOFFPACK_STUDENT"

    def __init__(self):
        # Fallback: Configuracion DB → ENV
        from ..models import Configuracion
        config = Configuracion.load()

        self.tenant = config.teams_tenant_id or settings.TEAMS_TENANT
        self.domain = settings.TEAMS_DOMAIN  # Domain siempre de ENV (no configurable en DB)
        self.client_id = config.teams_client_id or settings.TEAMS_CLIENT_ID
        self.client_secret = config.teams_client_secret or settings.TEAMS_CLIENT_SECRET
        self._token = None
        self._sku_id = None

    def _get_token(self) -> str:
        """
        Obtiene token OAuth2 usando Client Credentials Flow.
        El token se cachea para evitar múltiples llamadas.
        """
        if self._token:
            return self._token

        url = self.TOKEN_URL.format(tenant=self.tenant)
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }

        try:
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            self._token = result['access_token']
            logger.info("Token OAuth2 obtenido exitosamente")
            log_to_db('SUCCESS', 'teams_service', 'Token OAuth2 obtenido exitosamente')
            return self._token
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo token OAuth2: {e}")
            log_to_db('ERROR', 'teams_service', f'Error obteniendo token OAuth2: {e}')
            raise

    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers con autenticación para Graph API"""
        token = self._get_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def _get_student_sku_id(self) -> Optional[str]:
        """
        Obtiene el SKU ID de la licencia Microsoft 365 A1 para estudiantes.
        Busca por el partNumber del SKU.
        """
        if self._sku_id:
            return self._sku_id

        url = f"{self.BASE_URL}/subscribedSkus"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            skus = response.json().get('value', [])

            # Buscar el SKU de estudiantes
            for sku in skus:
                if sku.get('skuPartNumber') == self.STUDENT_SKU_PART_NUMBER:
                    self._sku_id = sku['skuId']
                    logger.info(f"SKU ID encontrado: {self._sku_id} ({self.STUDENT_SKU_PART_NUMBER})")
                    return self._sku_id

            # Si no se encuentra, listar todos los disponibles
            logger.warning(f"SKU '{self.STUDENT_SKU_PART_NUMBER}' no encontrado")
            logger.info("SKUs disponibles:")
            for sku in skus:
                logger.info(f"  - {sku.get('skuPartNumber')} (ID: {sku.get('skuId')})")

            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo SKU ID: {e}")
            return None

    def create_user(self, alumno) -> Optional[Dict]:
        """
        Crea usuario en Azure AD y asigna licencia de estudiante.

        Args:
            alumno: Instancia del modelo Alumno

        Returns:
            Dict con información del usuario creado o None si falla
        """
        # Generar UPN con prefijo según ENVIRONMENT_MODE
        prefix = settings.ACCOUNT_PREFIX  # "test-a" o "a"
        upn = f"{prefix}{alumno.dni}@{self.domain}"

        # Generar contraseña temporal
        password = self._generate_temp_password(alumno.dni)

        # Datos del usuario
        user_data = {
            "accountEnabled": True,
            "displayName": f"{alumno.apellido}, {alumno.nombre}",
            "givenName": alumno.nombre,
            "surname": alumno.apellido,
            "mailNickname": f"{prefix}{alumno.dni}",
            "userPrincipalName": upn,
            "passwordProfile": {
                "forceChangePasswordNextSignIn": True,
                "password": password
            },
            "usageLocation": "AR"  # Requerido para asignar licencias
        }

        url = f"{self.BASE_URL}/users"

        try:
            # Crear usuario
            logger.info(f"Creando usuario: {upn}")
            response = requests.post(
                url,
                json=user_data,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            user = response.json()
            logger.info(f"Usuario creado exitosamente: {upn} (ID: {user['id']})")
            log_to_db(
                'SUCCESS',
                'teams_service',
                f'Usuario creado exitosamente: {upn}',
                detalles={'user_id': user['id'], 'upn': upn},
                alumno=alumno
            )

            # Actualizar campos del alumno
            alumno.email_institucional = upn
            alumno.teams_password = password
            alumno.save(update_fields=['email_institucional', 'teams_password'])

            # Asignar licencia
            sku_id = self._get_student_sku_id()
            if sku_id:
                self._assign_license(user['id'], sku_id, alumno)
            else:
                logger.warning(f"No se pudo asignar licencia a {upn} - SKU no encontrado")
                log_to_db(
                    'WARNING',
                    'teams_service',
                    f'No se pudo asignar licencia a {upn} - SKU no encontrado',
                    alumno=alumno
                )

            # Retornar datos incluyendo la contraseña temporal
            return {
                'id': user['id'],
                'upn': upn,
                'displayName': user['displayName'],
                'password': password,
                'created': True
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_msg = e.response.json().get('error', {}).get('message', '')
                if 'already exists' in error_msg.lower():
                    logger.warning(f"Usuario {upn} ya existe")
                    log_to_db('WARNING', 'teams_service', f'Usuario {upn} ya existe', alumno=alumno)
                    return {'upn': upn, 'created': False, 'error': 'Usuario ya existe'}
                else:
                    logger.error(f"Error 400 creando usuario {upn}: {error_msg}")
                    log_to_db('ERROR', 'teams_service', f'Error 400 creando usuario {upn}: {error_msg}',
                             detalles={'status_code': 400, 'error': error_msg}, alumno=alumno)
            else:
                error_detail = str(e)
                logger.error(f"Error HTTP creando usuario {upn}: {e}")
                log_to_db('ERROR', 'teams_service', f'Error HTTP creando usuario {upn}',
                         detalles={'error': error_detail, 'status_code': e.response.status_code}, alumno=alumno)
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión creando usuario {upn}: {e}")
            log_to_db('ERROR', 'teams_service', f'Error de conexión creando usuario {upn}: {e}',
                     detalles={'error': str(e)}, alumno=alumno)
            return None

    def _assign_license(self, user_id: str, sku_id: str, alumno=None) -> bool:
        """
        Asigna licencia de estudiante a un usuario.

        Args:
            user_id: ID del usuario en Azure AD
            sku_id: ID del SKU de la licencia
            alumno: Instancia del modelo Alumno (opcional, para logging)

        Returns:
            True si se asignó exitosamente, False en caso contrario
        """
        url = f"{self.BASE_URL}/users/{user_id}/assignLicense"
        data = {
            "addLicenses": [
                {
                    "skuId": sku_id
                }
            ],
            "removeLicenses": []
        }

        try:
            logger.info(f"Asignando licencia {sku_id} a usuario {user_id}")
            response = requests.post(
                url,
                json=data,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Licencia asignada exitosamente a {user_id}")
            log_to_db('SUCCESS', 'teams_service', f'Licencia asignada exitosamente a usuario',
                     detalles={'user_id': user_id, 'sku_id': sku_id}, alumno=alumno)
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error asignando licencia a {user_id}: {e}")
            log_to_db('ERROR', 'teams_service', f'Error asignando licencia a usuario',
                     detalles={'user_id': user_id, 'sku_id': sku_id, 'error': str(e)}, alumno=alumno)
            return False

    def get_user(self, upn: str) -> Optional[Dict]:
        """
        Obtiene información de un usuario por su UPN.

        Args:
            upn: User Principal Name (email)

        Returns:
            Dict con información del usuario o None si no existe
        """
        url = f"{self.BASE_URL}/users/{upn}"

        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            user = response.json()
            logger.info(f"Usuario encontrado: {upn}")
            return user
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.info(f"Usuario no encontrado: {upn}")
                return None
            logger.error(f"Error obteniendo usuario {upn}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión obteniendo usuario {upn}: {e}")
            return None

    def reset_password(self, upn: str, new_password: Optional[str] = None) -> Optional[str]:
        """
        Resetea la contraseña de un usuario.

        Args:
            upn: User Principal Name (email)
            new_password: Nueva contraseña (si es None, se genera una automática)

        Returns:
            Nueva contraseña o None si falla
        """
        # Generar contraseña si no se proporcionó
        if not new_password:
            dni = upn.split('@')[0].replace(settings.ACCOUNT_PREFIX, '')
            new_password = self._generate_temp_password(dni)

        url = f"{self.BASE_URL}/users/{upn}"
        data = {
            "passwordProfile": {
                "forceChangePasswordNextSignIn": True,
                "password": new_password
            }
        }

        try:
            logger.info(f"Reseteando contraseña de {upn}")
            response = requests.patch(
                url,
                json=data,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Contraseña reseteada exitosamente para {upn}")
            return new_password
        except requests.exceptions.RequestException as e:
            logger.error(f"Error reseteando contraseña de {upn}: {e}")
            return None

    def list_test_users(self) -> List[Dict]:
        """
        Lista todos los usuarios con prefijo test-a (para testing).
        Útil para limpieza de cuentas de prueba.

        Returns:
            Lista de usuarios test-*
        """
        url = f"{self.BASE_URL}/users"
        params = {
            '$filter': f"startswith(userPrincipalName, 'test-a')",
            '$select': 'id,userPrincipalName,displayName'
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            users = response.json().get('value', [])
            logger.info(f"Encontrados {len(users)} usuarios test-*")
            return users
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listando usuarios test-*: {e}")
            return []

    def delete_user(self, upn: str) -> bool:
        """
        Elimina un usuario de Azure AD.
        PRECAUCIÓN: Solo usar para cuentas test-*

        Args:
            upn: User Principal Name (email)

        Returns:
            True si se eliminó exitosamente, False en caso contrario
        """
        # Verificación de seguridad: solo permitir eliminar cuentas test-*
        if not upn.startswith('test-'):
            logger.error(f"SEGURIDAD: Intento de eliminar cuenta no-test: {upn}")
            return False

        url = f"{self.BASE_URL}/users/{upn}"

        try:
            logger.info(f"Eliminando usuario: {upn}")
            response = requests.delete(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            logger.info(f"Usuario eliminado exitosamente: {upn}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error eliminando usuario {upn}: {e}")
            return False

    @staticmethod
    def _generate_temp_password(dni: str) -> str:
        """
        Genera contraseña temporal segura basada en el DNI.
        Formato: Unrc2025!{dni}

        Args:
            dni: DNI del alumno

        Returns:
            Contraseña temporal
        """
        return f"Unrc2025!{dni}"
