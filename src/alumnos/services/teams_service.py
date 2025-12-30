"""
Nombre del Módulo: teams_service.py

Descripción:
Servicio de integración con Microsoft Teams.

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

import requests
import logging
from typing import Optional, Dict, List
from urllib.parse import quote
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
        self.account_prefix = config.account_prefix or settings.ACCOUNT_PREFIX
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
        except requests.exceptions.HTTPError as e:
            error_detail = f"{e}"
            if e.response.status_code == 400:
                error_detail = "Credenciales inválidas (tenant_id, client_id o client_secret incorrectos)"
            logger.error(f"Error obteniendo token OAuth2: {error_detail}")
            log_to_db('ERROR', 'teams_service', f'Error obteniendo token OAuth2: {error_detail}')
            raise ValueError(f"T-002: {error_detail}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo token OAuth2: {e}")
            log_to_db('ERROR', 'teams_service', f'Error obteniendo token OAuth2: {e}')
            raise ValueError(f"T-002: Error de conexión - {e}") from e

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
        Busca usuario en Azure AD y lo crea solo si no existe.
        Si ya existe, retorna la información del usuario existente.

        Args:
            alumno: Instancia del modelo Alumno

        Returns:
            Dict con información del usuario (created=True si fue creado, False si ya existía)
        """
        # Generar UPN con prefijo desde configuración
        prefix = self.account_prefix  # Desde BD o settings
        upn = f"{prefix}{alumno.dni}@{self.domain}"

        # 1. BUSCAR PRIMERO si el usuario ya existe
        logger.info(f"Buscando usuario existente: {upn}")
        existing_user = self.get_user(upn)

        if existing_user:
            logger.info(f"Usuario ya existe: {upn} (ID: {existing_user['id']})")
            log_to_db(
                'INFO',
                'teams_service',
                f'Usuario ya existe en Teams: {upn}',
                detalles={'user_id': existing_user['id'], 'upn': upn},
                alumno=alumno
            )

            # Actualizar UPN en BD si no lo tiene
            if not alumno.email_institucional:
                alumno.email_institucional = upn
                alumno.save(update_fields=['email_institucional'])

            # Retornar usuario existente
            return {
                'id': existing_user['id'],
                'upn': upn,
                'displayName': existing_user.get('displayName'),
                'password': alumno.teams_password,  # Usar password guardada en BD
                'created': False,  # No fue creado ahora
                'already_exists': True
            }

        # 2. Si NO existe, crear usuario nuevo
        logger.info(f"Usuario no existe, creando: {upn}")

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
                # Manejar caso donde 'error' puede ser string o dict
                error_data = e.response.json().get('error', {})
                if isinstance(error_data, dict):
                    error_msg = error_data.get('message', '')
                else:
                    error_msg = str(error_data)

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
        # URL encode del UPN para manejar caracteres especiales como @
        upn_encoded = quote(upn, safe='')
        url = f"{self.BASE_URL}/users/{upn_encoded}"

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

    def reset_password(self, upn: str, new_password: Optional[str] = None, alumno=None) -> Optional[str]:
        """
        Resetea la contraseña de un usuario.

        Args:
            upn: User Principal Name (email)
            new_password: Nueva contraseña (si es None, se genera una automática)
            alumno: Instancia del modelo Alumno (opcional, para logging)

        Returns:
            Nueva contraseña o None si falla
        """
        # Generar contraseña si no se proporcionó
        if not new_password:
            dni = upn.split('@')[0].replace(self.account_prefix, '')
            new_password = self._generate_temp_password(dni)

        # URL encode del UPN para manejar caracteres especiales como @
        upn_encoded = quote(upn, safe='')
        url = f"{self.BASE_URL}/users/{upn_encoded}"
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
            log_to_db('SUCCESS', 'teams_service', f'Contraseña reseteada exitosamente: {upn}', alumno=alumno)

            # Guardar nueva password en el modelo Alumno
            if alumno:
                alumno.teams_password = new_password
                alumno.save(update_fields=['teams_password'])

            return new_password
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Usuario no encontrado para resetear: {upn}")
                log_to_db('WARNING', 'teams_service', f'Usuario no encontrado: {upn}', alumno=alumno)
                raise ValueError(f"T-007: Usuario no encontrado en Teams")
            else:
                logger.error(f"Error HTTP reseteando contraseña {upn}: {e}")
                log_to_db('ERROR', 'teams_service', f'Error HTTP reseteando contraseña {upn}',
                         detalles={'error': str(e), 'status_code': e.response.status_code}, alumno=alumno)
                raise ValueError(f"T-006: Error al resetear contraseña - {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión reseteando contraseña de {upn}: {e}")
            log_to_db('ERROR', 'teams_service', f'Error de conexión reseteando contraseña {upn}',
                     detalles={'error': str(e)}, alumno=alumno)
            raise ValueError(f"T-009: Error de conexión - {e}")

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

    def delete_user(self, upn: str, alumno=None) -> bool:
        """
        Elimina un usuario de Azure AD.
        PRECAUCIÓN: Solo usar para cuentas test-*

        Args:
            upn: User Principal Name (email)
            alumno: Instancia del modelo Alumno (opcional, para logging)

        Returns:
            True si se eliminó exitosamente, False en caso contrario
        """
        # Verificación de seguridad: solo permitir eliminar cuentas test-*
        #if not upn.startswith('test-'):
        #    logger.error(f"SEGURIDAD: Intento de eliminar cuenta no-test: {upn}")
        #     log_to_db('ERROR', 'teams_service', f'SEGURIDAD: Intento de eliminar cuenta no-test: {upn}', alumno=alumno)
        #    raise ValueError(f"T-999: Por seguridad, solo se pueden eliminar cuentas test-*")

        # URL encode del UPN para manejar caracteres especiales como @
        upn_encoded = quote(upn, safe='')
        url = f"{self.BASE_URL}/users/{upn_encoded}"

        try:
            logger.info(f"Eliminando usuario: {upn}")
            response = requests.delete(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            logger.info(f"Usuario eliminado exitosamente: {upn}")
            log_to_db('SUCCESS', 'teams_service', f'Usuario eliminado exitosamente: {upn}', alumno=alumno)
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Usuario no encontrado para eliminar: {upn}")
                log_to_db('WARNING', 'teams_service', f'Usuario no encontrado: {upn}', alumno=alumno)
                raise ValueError(f"T-007: Usuario no encontrado en Teams")
            else:
                logger.error(f"Error HTTP eliminando usuario {upn}: {e}")
                log_to_db('ERROR', 'teams_service', f'Error HTTP eliminando usuario {upn}',
                         detalles={'error': str(e), 'status_code': e.response.status_code}, alumno=alumno)
                raise ValueError(f"T-003: Error al eliminar usuario en Teams - {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión eliminando usuario {upn}: {e}")
            log_to_db('ERROR', 'teams_service', f'Error de conexión eliminando usuario {upn}',
                     detalles={'error': str(e)}, alumno=alumno)
            raise ValueError(f"T-009: Error de conexión - {e}")

    @staticmethod
    def _generate_temp_password(dni: str = None) -> str:
        """
        Genera contraseña temporal completamente aleatoria que cumple con los estándares de Microsoft.

        Requisitos de Microsoft:
        - Mínimo 8 caracteres
        - Al menos 3 de estas 4 categorías: mayúsculas, minúsculas, números, símbolos

        Genera una password de 16 caracteres con:
        - 4 mayúsculas
        - 4 minúsculas
        - 4 dígitos
        - 4 símbolos especiales

        Args:
            dni: DNI del alumno (no se usa, mantenido por compatibilidad)

        Returns:
            Contraseña temporal aleatoria
        """
        import secrets
        import string

        # Generar caracteres aleatorios de cada categoría
        uppercase = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(4))
        lowercase = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(4))
        digits = ''.join(secrets.choice(string.digits) for _ in range(4))
        symbols = ''.join(secrets.choice('!@#$%^&*') for _ in range(4))

        # Combinar todos los caracteres
        all_chars = list(uppercase + lowercase + digits + symbols)

        # Mezclar aleatoriamente
        secrets.SystemRandom().shuffle(all_chars)

        return ''.join(all_chars)
