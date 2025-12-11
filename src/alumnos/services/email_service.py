"""
Servicio de envío de emails para notificaciones a alumnos.

Funcionalidades:
- Enviar credenciales de acceso (Teams)
- Emails de bienvenida
- Confirmaciones de enrolamiento
- Notificaciones de cambio de estado
"""
import logging
from typing import Optional
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

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


class EmailService:
    """Cliente SMTP para envío de emails a alumnos"""

    def __init__(self):
        # Fallback: Configuracion DB → ENV
        from ..models import Configuracion
        config = Configuracion.load()

        self.from_email = config.email_from or settings.DEFAULT_FROM_EMAIL
        self.email_host = config.email_host or settings.EMAIL_HOST
        self.email_port = config.email_port if config.email_port is not None else settings.EMAIL_PORT
        self.email_use_tls = config.email_use_tls if config.email_use_tls is not None else settings.EMAIL_USE_TLS

    def send_credentials_email(self, alumno, teams_data: dict) -> bool:
        """
        Envía email con credenciales de acceso a Teams.

        Args:
            alumno: Instancia del modelo Alumno
            teams_data: Dict con datos de Teams (upn, password)

        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        upn = teams_data.get('upn')
        password = teams_data.get('password')

        if not upn or not password:
            logger.error(f"Datos incompletos para enviar credenciales a {alumno.email}")
            return False

        subject = "Credenciales de acceso - UNRC"

        # Mensaje en texto plano
        message = f"""
Hola {alumno.nombre} {alumno.apellido},

Te damos la bienvenida a la Universidad Nacional de Río Cuarto.

Tus credenciales de acceso a Microsoft Teams y servicios institucionales son:

Usuario: {upn}
Contraseña temporal: {password}

IMPORTANTE:
- La primera vez que ingreses, se te pedirá cambiar la contraseña
- Guarda tu nueva contraseña en un lugar seguro
- Si olvidaste tu contraseña, contacta a soporte técnico

Accede a Teams en: https://teams.microsoft.com

Saludos,
Sistema Lucy AMS
Universidad Nacional de Río Cuarto

---
Este es un mensaje automático, por favor no responder.
"""

        # Mensaje HTML (opcional, más visual)
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #003366; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .credentials {{ background-color: #e8f4f8; padding: 15px; border-left: 4px solid #003366; margin: 20px 0; }}
        .credentials strong {{ color: #003366; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #003366; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }}
        .warning {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Bienvenido/a a la UNRC</h1>
        </div>

        <div class="content">
            <h2>Hola {alumno.nombre} {alumno.apellido},</h2>

            <p>Te damos la bienvenida a la <strong>Universidad Nacional de Río Cuarto</strong>.</p>

            <p>Tus credenciales de acceso a Microsoft Teams y servicios institucionales son:</p>

            <div class="credentials">
                <p><strong>Usuario:</strong> {upn}</p>
                <p><strong>Contraseña temporal:</strong> {password}</p>
            </div>

            <div class="warning">
                <strong>⚠️ IMPORTANTE:</strong>
                <ul>
                    <li>La primera vez que ingreses, se te pedirá cambiar la contraseña</li>
                    <li>Guarda tu nueva contraseña en un lugar seguro</li>
                    <li>Si olvidaste tu contraseña, contacta a soporte técnico</li>
                </ul>
            </div>

            <p style="text-align: center;">
                <a href="https://teams.microsoft.com" class="button">Acceder a Teams</a>
            </p>

            <p>Si tienes alguna consulta, no dudes en contactarte con soporte técnico.</p>

            <p>Saludos,<br>
            <strong>Sistema Lucy AMS</strong><br>
            Universidad Nacional de Río Cuarto</p>
        </div>

        <div class="footer">
            Este es un mensaje automático, por favor no responder.<br>
            Universidad Nacional de Río Cuarto - Río Cuarto, Argentina
        </div>
    </div>
</body>
</html>
"""

        try:
            logger.info(f"Enviando credenciales a {alumno.email} (UPN: {upn})")

            result = send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=[alumno.email],
                html_message=html_message,
                fail_silently=False
            )

            if result == 1:
                logger.info(f"Email enviado exitosamente a {alumno.email}")
                log_to_db('SUCCESS', 'email_service', f'Email de credenciales enviado exitosamente a {alumno.email}',
                         detalles={'email': alumno.email, 'upn': upn}, alumno=alumno)
                return True
            else:
                logger.warning(f"send_mail retornó {result} para {alumno.email}")
                log_to_db('WARNING', 'email_service', f'send_mail retornó {result} para {alumno.email}',
                         alumno=alumno)
                return False

        except Exception as e:
            logger.error(f"Error enviando email a {alumno.email}: {e}")
            log_to_db('ERROR', 'email_service', f'Error enviando email a {alumno.email}',
                     detalles={'error': str(e)}, alumno=alumno)
            return False

    def send_welcome_email(self, alumno) -> bool:
        """
        Envía email de bienvenida a aspirantes (sin credenciales aún).

        Args:
            alumno: Instancia del modelo Alumno

        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        subject = "Bienvenido/a a la UNRC"

        message = f"""
Hola {alumno.nombre} {alumno.apellido},

Te damos la bienvenida a la Universidad Nacional de Río Cuarto.

En breve recibirás un email con tus credenciales de acceso a los servicios institucionales.

Saludos,
Sistema Lucy AMS
Universidad Nacional de Río Cuarto
"""

        try:
            logger.info(f"Enviando email de bienvenida a {alumno.email}")

            result = send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=[alumno.email],
                fail_silently=False
            )

            if result == 1:
                logger.info(f"Email de bienvenida enviado a {alumno.email}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error enviando email de bienvenida a {alumno.email}: {e}")
            return False

    def send_enrollment_confirmation(self, alumno, curso: str) -> bool:
        """
        Envía confirmación de enrolamiento en un curso.

        Args:
            alumno: Instancia del modelo Alumno
            curso: Nombre del curso

        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        subject = f"Confirmación de enrolamiento - {curso}"

        message = f"""
Hola {alumno.nombre} {alumno.apellido},

Te confirmamos tu enrolamiento en el curso:

{curso}

Ya puedes acceder al curso en Moodle con tus credenciales institucionales.

Saludos,
Sistema Lucy AMS
Universidad Nacional de Río Cuarto
"""

        try:
            logger.info(f"Enviando confirmación de enrolamiento a {alumno.email}")

            result = send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=[alumno.email],
                fail_silently=False
            )

            if result == 1:
                logger.info(f"Confirmación de enrolamiento enviada a {alumno.email}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error enviando confirmación a {alumno.email}: {e}")
            return False

    def send_status_change_email(self, alumno, old_status: str, new_status: str) -> bool:
        """
        Envía notificación de cambio de estado del alumno.

        Args:
            alumno: Instancia del modelo Alumno
            old_status: Estado anterior
            new_status: Nuevo estado

        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        subject = "Actualización de estado - UNRC"

        message = f"""
Hola {alumno.nombre} {alumno.apellido},

Te informamos que tu estado ha sido actualizado:

Estado anterior: {old_status}
Nuevo estado: {new_status}

Si tienes consultas, contacta con la administración académica.

Saludos,
Sistema Lucy AMS
Universidad Nacional de Río Cuarto
"""

        try:
            logger.info(f"Enviando notificación de cambio de estado a {alumno.email}")

            result = send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=[alumno.email],
                fail_silently=False
            )

            if result == 1:
                logger.info(f"Notificación enviada a {alumno.email}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error enviando notificación a {alumno.email}: {e}")
            return False
