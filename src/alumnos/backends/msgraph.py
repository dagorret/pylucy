"""
Backend de email para Django usando Microsoft Graph API.

Este backend utiliza la API de Microsoft Graph para enviar emails
a través de Microsoft 365 / Azure AD, como alternativa al SMTP tradicional.

Ventajas sobre SMTP:
- No requiere habilitar SMTP en Exchange/Office 365
- Mejor control de errores y seguimiento
- Integración nativa con Azure AD
- Soporta características avanzadas de Microsoft 365

Configuración requerida:
- TEAMS_TENANT: Tenant ID de Azure AD (reutiliza la config de Teams)
- TEAMS_CLIENT_ID: Client ID de la aplicación
- TEAMS_CLIENT_SECRET: Client Secret
- DEFAULT_FROM_EMAIL: Email del usuario que enviará los correos

Permisos requeridos en Azure AD (Application permissions):
- Mail.Send: Permite enviar emails como cualquier usuario
"""
import requests
import logging
from typing import List, Optional
from django.core.mail.backends.base import BaseEmailBackend
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


class MicrosoftGraphEmailBackend(BaseEmailBackend):
    """
    Backend de email que usa Microsoft Graph API para enviar correos.

    Este backend reemplaza el SMTP tradicional utilizando la API REST
    de Microsoft Graph para enviar emails a través de Microsoft 365.
    """

    BASE_URL = "https://graph.microsoft.com/v1.0"
    TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    def __init__(self, fail_silently=False, **kwargs):
        """
        Inicializa el backend con configuración desde BD o variables de entorno.

        Args:
            fail_silently: Si es True, suprime excepciones de envío
            **kwargs: Argumentos adicionales del backend base
        """
        super().__init__(fail_silently=fail_silently, **kwargs)

        # Fallback: Configuracion DB → ENV (mismo patrón que teams_service.py)
        from ..models import Configuracion
        config = Configuracion.load()

        self.tenant = config.teams_tenant_id or getattr(settings, 'TEAMS_TENANT', None)
        self.client_id = config.teams_client_id or getattr(settings, 'TEAMS_CLIENT_ID', None)
        self.client_secret = config.teams_client_secret or getattr(settings, 'TEAMS_CLIENT_SECRET', None)
        self.from_email = config.email_from or getattr(settings, 'DEFAULT_FROM_EMAIL', None)

        # Cache del token OAuth2
        self._token = None

        # Validar configuración requerida
        if not all([self.tenant, self.client_id, self.client_secret, self.from_email]):
            logger.warning(
                "MicrosoftGraphEmailBackend: Configuración incompleta. "
                "Asegúrate de configurar TEAMS_TENANT, TEAMS_CLIENT_ID, "
                "TEAMS_CLIENT_SECRET y DEFAULT_FROM_EMAIL"
            )

    def _get_token(self) -> str:
        """
        Obtiene token OAuth2 usando Client Credentials Flow.
        El token se cachea en memoria durante la instancia del backend.

        Returns:
            str: Access token para Microsoft Graph API

        Raises:
            ValueError: Si las credenciales son inválidas o hay error de conexión
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
            logger.info("MicrosoftGraphEmailBackend: Token OAuth2 obtenido exitosamente")
            log_to_db('SUCCESS', 'msgraph_backend', 'Token OAuth2 obtenido exitosamente')
            return self._token
        except requests.exceptions.HTTPError as e:
            error_detail = str(e)
            if e.response.status_code == 400:
                error_detail = "Credenciales inválidas (tenant_id, client_id o client_secret incorrectos)"
            logger.error(f"MicrosoftGraphEmailBackend: Error obteniendo token: {error_detail}")
            log_to_db('ERROR', 'msgraph_backend', f'Error obteniendo token OAuth2: {error_detail}')
            if not self.fail_silently:
                raise ValueError(f"MSGraph-001: {error_detail}") from e
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"MicrosoftGraphEmailBackend: Error de conexión: {e}")
            log_to_db('ERROR', 'msgraph_backend', f'Error de conexión OAuth2: {e}')
            if not self.fail_silently:
                raise ValueError(f"MSGraph-002: Error de conexión - {e}") from e
            return None

    def _get_headers(self) -> dict:
        """
        Retorna headers HTTP con autenticación para Graph API.

        Returns:
            dict: Headers con Authorization y Content-Type
        """
        token = self._get_token()
        if not token:
            return {}

        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def _convert_email_message(self, message) -> dict:
        """
        Convierte un EmailMessage de Django al formato de Microsoft Graph API.

        Args:
            message: Instancia de django.core.mail.EmailMessage

        Returns:
            dict: Payload en formato Microsoft Graph para sendMail
        """
        # Determinar tipo de contenido (HTML o texto plano)
        # EmailMessage tiene .body (texto) y opcionalmente alternativas HTML
        content_type = "Text"
        body_content = message.body

        # Verificar si hay contenido HTML en alternatives
        if hasattr(message, 'alternatives') and message.alternatives:
            for alternative_content, alternative_type in message.alternatives:
                if alternative_type == 'text/html':
                    content_type = "HTML"
                    body_content = alternative_content
                    break

        # Construir lista de destinatarios
        to_recipients = [
            {"emailAddress": {"address": recipient}}
            for recipient in message.to
        ]

        # Construir lista de CC (si existe)
        cc_recipients = []
        if hasattr(message, 'cc') and message.cc:
            cc_recipients = [
                {"emailAddress": {"address": recipient}}
                for recipient in message.cc
            ]

        # Construir lista de BCC (si existe)
        bcc_recipients = []
        if hasattr(message, 'bcc') and message.bcc:
            bcc_recipients = [
                {"emailAddress": {"address": recipient}}
                for recipient in message.bcc
            ]

        # Construir payload de Microsoft Graph
        graph_message = {
            "message": {
                "subject": message.subject,
                "body": {
                    "contentType": content_type,
                    "content": body_content
                },
                "toRecipients": to_recipients,
            },
            "saveToSentItems": True
        }

        # Agregar CC si existe
        if cc_recipients:
            graph_message["message"]["ccRecipients"] = cc_recipients

        # Agregar BCC si existe
        if bcc_recipients:
            graph_message["message"]["bccRecipients"] = bcc_recipients

        # Agregar Reply-To si existe
        if hasattr(message, 'reply_to') and message.reply_to:
            graph_message["message"]["replyTo"] = [
                {"emailAddress": {"address": reply_to}}
                for reply_to in message.reply_to
            ]

        return graph_message

    def send_messages(self, email_messages) -> int:
        """
        Envía uno o más EmailMessage usando Microsoft Graph API.

        Este método es llamado por Django cuando se usa send_mail() o send_mass_mail().

        Args:
            email_messages: Lista de instancias de django.core.mail.EmailMessage

        Returns:
            int: Número de emails enviados exitosamente
        """
        if not email_messages:
            return 0

        # Obtener headers con token
        headers = self._get_headers()
        if not headers:
            logger.error("MicrosoftGraphEmailBackend: No se pudo obtener token de autenticación")
            return 0

        num_sent = 0

        for message in email_messages:
            try:
                # Convertir mensaje de Django a formato Graph API
                graph_payload = self._convert_email_message(message)

                # Endpoint de envío de email
                # Usamos el email configurado en from_email como sender
                sender_email = message.from_email or self.from_email
                url = f"{self.BASE_URL}/users/{sender_email}/sendMail"

                # Enviar email vía Graph API
                response = requests.post(
                    url,
                    headers=headers,
                    json=graph_payload,
                    timeout=30
                )
                response.raise_for_status()

                # Graph API retorna 202 Accepted en éxito (sin cuerpo)
                num_sent += 1
                logger.info(
                    f"MicrosoftGraphEmailBackend: Email enviado exitosamente a {message.to} "
                    f"(asunto: {message.subject})"
                )
                log_to_db(
                    'SUCCESS',
                    'msgraph_backend',
                    f'Email enviado a {", ".join(message.to)}',
                    detalles=f'Asunto: {message.subject}'
                )

            except requests.exceptions.HTTPError as e:
                error_msg = f"Error HTTP {e.response.status_code}"
                try:
                    error_detail = e.response.json()
                    error_msg = f"{error_msg}: {error_detail.get('error', {}).get('message', str(e))}"
                except:
                    error_msg = f"{error_msg}: {str(e)}"

                logger.error(
                    f"MicrosoftGraphEmailBackend: Error enviando email a {message.to}: {error_msg}"
                )
                log_to_db(
                    'ERROR',
                    'msgraph_backend',
                    f'Error enviando email a {", ".join(message.to)}',
                    detalles=error_msg
                )

                if not self.fail_silently:
                    raise

            except requests.exceptions.RequestException as e:
                error_msg = f"Error de conexión: {str(e)}"
                logger.error(
                    f"MicrosoftGraphEmailBackend: {error_msg} al enviar a {message.to}"
                )
                log_to_db(
                    'ERROR',
                    'msgraph_backend',
                    f'Error de conexión enviando email a {", ".join(message.to)}',
                    detalles=error_msg
                )

                if not self.fail_silently:
                    raise

            except Exception as e:
                error_msg = f"Error inesperado: {str(e)}"
                logger.error(
                    f"MicrosoftGraphEmailBackend: {error_msg} al enviar a {message.to}"
                )
                log_to_db(
                    'ERROR',
                    'msgraph_backend',
                    f'Error inesperado enviando email a {", ".join(message.to)}',
                    detalles=error_msg
                )

                if not self.fail_silently:
                    raise

        return num_sent
