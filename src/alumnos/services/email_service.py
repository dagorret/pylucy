"""
Nombre del Módulo: email_service.py

Descripción:
Servicio para envío de emails.

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

        🔧 REPARACIÓN: Usa plantilla desde Configuracion.email_plantilla_credenciales (BD > .env)

        Args:
            alumno: Instancia del modelo Alumno
            teams_data: Dict con datos de Teams (upn, password)

        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        from ..models import Configuracion
        config = Configuracion.load()

        upn = teams_data.get('upn')
        password = teams_data.get('password')

        if not upn or not password:
            logger.error(f"Datos incompletos para enviar credenciales a {alumno.email}")
            return False

        # 🔧 ASUNTO DINÁMICO DESDE BD
        subject = config.email_asunto_credenciales or "Credenciales de acceso - UNRC"
        try:
            subject = subject.format(
                nombre=alumno.nombre,
                apellido=alumno.apellido,
                upn=upn
            )
        except KeyError:
            pass  # Si hay error en el formato, usar el subject sin formatear

        # 🔧 USAR PLANTILLA DESDE BD O FALLBACK A TEXTO DEFAULT
        plantilla = config.email_plantilla_credenciales
        if plantilla:
            # Reemplazar variables en la plantilla
            try:
                message = plantilla.format(
                    nombre=alumno.nombre,
                    apellido=alumno.apellido,
                    dni=alumno.dni,
                    email=alumno.email_personal or alumno.email_institucional or '',
                    upn=upn,
                    password=password,
                )
                # Si la plantilla es HTML, usarla como html_message
                html_message = message if '<html' in plantilla.lower() else None
            except KeyError as e:
                logger.error(f"Error en variables de plantilla: {e}")
                plantilla = None

        if not plantilla:
            # Fallback si no hay plantilla configurada
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

        # Si no hay plantilla personalizada, no enviar html_message (solo texto plano)
        if not html_message:
            html_message = None

        try:
            # IMPORTANTE: Siempre enviar al email_personal
            email_destino = alumno.email_personal or alumno.email_institucional
            if not email_destino:
                logger.error(f"Alumno {alumno.id} no tiene email personal ni institucional")
                return False

            logger.info(f"Enviando credenciales a {email_destino} (email personal) (UPN: {upn})")

            result = send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=[email_destino],
                html_message=html_message,
                fail_silently=False
            )

            if result == 1:
                logger.info(f"Email de credenciales enviado exitosamente a {email_destino}")
                log_to_db('SUCCESS', 'email_service', f'Email de credenciales enviado a email personal: {email_destino}',
                         detalles={'email_personal': email_destino, 'upn': upn}, alumno=alumno)
                return True
            else:
                logger.warning(f"send_mail retornó {result} para {email_destino}")
                log_to_db('WARNING', 'email_service', f'send_mail retornó {result} para {email_destino}',
                         alumno=alumno)
                return False

        except Exception as e:
            logger.error(f"Error enviando email a {email_destino}: {e}")
            log_to_db('ERROR', 'email_service', f'Error enviando email a {alumno.email}',
                     detalles={'error': str(e)}, alumno=alumno)
            return False

    def send_welcome_email(self, alumno) -> bool:
        """
        Envía email de bienvenida a aspirantes (sin credenciales aún).

        🔧 REPARACIÓN: Usa plantilla desde Configuracion.email_plantilla_bienvenida (BD > .env)

        Args:
            alumno: Instancia del modelo Alumno

        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        from ..models import Configuracion
        config = Configuracion.load()

        # 🔧 ASUNTO DINÁMICO DESDE BD
        subject = config.email_asunto_bienvenida or "Bienvenido/a a la UNRC"
        try:
            subject = subject.format(
                nombre=alumno.nombre,
                apellido=alumno.apellido,
                dni=alumno.dni
            )
        except KeyError:
            pass

        # 🔧 USAR PLANTILLA DESDE BD O FALLBACK A TEXTO DEFAULT
        plantilla = config.email_plantilla_bienvenida
        html_message = None
        if plantilla:
            # Reemplazar variables en la plantilla
            try:
                message = plantilla.format(
                    nombre=alumno.nombre,
                    apellido=alumno.apellido,
                    dni=alumno.dni,
                    email=alumno.email_personal or alumno.email_institucional or '',
                )
                # Si la plantilla es HTML, usarla como html_message
                html_message = message if '<html' in plantilla.lower() else None
            except KeyError as e:
                logger.error(f"Error en variables de plantilla: {e}")
                plantilla = None

        if not plantilla:
            # Fallback si no hay plantilla configurada
            message = f"""
Hola {alumno.nombre} {alumno.apellido},

Te damos la bienvenida a la Universidad Nacional de Río Cuarto.

En breve recibirás un email con tus credenciales de acceso a los servicios institucionales.

Saludos,
Sistema Lucy AMS
Universidad Nacional de Río Cuarto
"""

        try:
            # IMPORTANTE: Siempre enviar al email_personal
            email_destino = alumno.email_personal or alumno.email_institucional
            if not email_destino:
                logger.error(f"Alumno {alumno.id} no tiene email personal ni institucional")
                return False

            logger.info(f"Enviando email de bienvenida a {email_destino} (email personal)")

            result = send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=[email_destino],
                html_message=html_message,  # Agregar HTML
                fail_silently=False
            )

            if result == 1:
                logger.info(f"Email de bienvenida enviado a {email_destino}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error enviando email de bienvenida a {alumno.email}: {e}")
            return False

    def send_enrollment_email(self, alumno, courses_enrolled: list = None) -> bool:
        """
        Envía email de enrollamiento en Moodle (Ecosistema Virtual).

        Explica:
        - Acceso a v.eco.unrc.edu.ar
        - Login con credenciales de Teams (UPN + contraseña Teams)
        - Cursos en los que fue enrollado

        Args:
            alumno: Instancia del modelo Alumno
            courses_enrolled: Lista de shortnames de cursos enrollados

        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        from ..models import Configuracion
        config = Configuracion.load()

        moodle_url = config.moodle_base_url or "https://v.eco.unrc.edu.ar"
        upn = alumno.email_institucional or f"{alumno.dni}@eco.unrc.edu.ar"

        # Lista de cursos
        if courses_enrolled and len(courses_enrolled) > 0:
            cursos_html = "<ul>" + "".join([f"<li>{curso}</li>" for curso in courses_enrolled]) + "</ul>"
            cursos_texto = "\n".join([f"- {curso}" for curso in courses_enrolled])
        else:
            cursos_html = "<p><em>Serás notificado cuando los cursos estén disponibles.</em></p>"
            cursos_texto = "Serás notificado cuando los cursos estén disponibles."

        # 🔧 ASUNTO DINÁMICO DESDE BD
        subject = config.email_asunto_enrollamiento or "Acceso al Ecosistema Virtual - UNRC"
        try:
            subject = subject.format(
                nombre=alumno.nombre,
                apellido=alumno.apellido
            )
        except KeyError:
            pass

        # 🔧 USAR PLANTILLA DESDE BD O FALLBACK A TEXTO DEFAULT
        plantilla = config.email_plantilla_enrollamiento
        html_message = None
        password = alumno.teams_password or "[Contactar soporte]"

        if plantilla:
            try:
                message = plantilla.format(
                    nombre=alumno.nombre,
                    apellido=alumno.apellido,
                    upn=upn,
                    password=password,
                    moodle_url=moodle_url,
                    cursos_html=cursos_html,
                    cursos_texto=cursos_texto
                )
                # Si la plantilla es HTML, usarla como html_message
                html_message = message if '<html' in plantilla.lower() else None
            except KeyError as e:
                logger.error(f"Error en variables de plantilla de enrollamiento: {e}")
                plantilla = None

        if not plantilla:
            # Mensaje en texto plano (fallback)
            message = f"""
Hola {alumno.nombre} {alumno.apellido},

¡Bienvenido/a al Ecosistema Virtual de la Facultad de Ciencias Económicas!

Has sido enrollado/a en nuestro campus virtual Moodle.

🌐 ACCESO AL ECOSISTEMA VIRTUAL:
URL: {moodle_url}

🔑 CREDENCIALES DE ACCESO:
Usuario: {upn}
Contraseña: {password}

IMPORTANTE:
- Estas son las mismas credenciales para Microsoft Teams y el Campus Virtual
- En el primer acceso deberás cambiar tu contraseña
- El acceso es mediante autenticación de Microsoft (OpenID Connect)
- Guarda estas credenciales en un lugar seguro

📚 CURSOS ENROLLADOS:
{cursos_texto}

Si tienes alguna consulta o problema para acceder, contacta con soporte técnico.

Saludos,
Sistema Lucy AMS
Facultad de Ciencias Económicas
Universidad Nacional de Río Cuarto

---
Este es un mensaje automático, por favor no responder.
"""
            # Generar versión HTML del fallback
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #003366; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; }}
        .credentials {{ background-color: #e8f4f8; border-left: 4px solid #0066cc; padding: 15px; margin: 20px 0; }}
        .important {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
        .courses {{ background-color: #fff; padding: 15px; margin: 20px 0; border: 1px solid #ddd; }}
        .footer {{ background-color: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
        ul {{ padding-left: 20px; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Ecosistema Virtual FCE - UNRC</h1>
        </div>

        <div class="content">
            <p>Hola <strong>{alumno.nombre} {alumno.apellido}</strong>,</p>

            <p>¡Bienvenido/a al <strong>Ecosistema Virtual de la Facultad de Ciencias Económicas</strong>!</p>

            <p>Has sido enrollado/a en nuestro campus virtual Moodle.</p>

            <h3>🌐 ACCESO AL ECOSISTEMA VIRTUAL</h3>
            <p>URL: <a href="{moodle_url}">{moodle_url}</a></p>

            <div class="credentials">
                <h3>🔑 CREDENCIALES DE ACCESO</h3>
                <p><strong>Usuario:</strong> {upn}</p>
                <p><strong>Contraseña:</strong> {password}</p>
            </div>

            <div class="important">
                <h3>⚠️ IMPORTANTE</h3>
                <ul>
                    <li>Estas son las mismas credenciales para Microsoft Teams y el Campus Virtual</li>
                    <li>En el primer acceso deberás cambiar tu contraseña</li>
                    <li>El acceso es mediante autenticación de Microsoft (OpenID Connect)</li>
                    <li>Guarda estas credenciales en un lugar seguro</li>
                </ul>
            </div>

            <div class="courses">
                <h3>📚 CURSOS ENROLLADOS</h3>
                {cursos_html}
            </div>

            <p>Si tienes alguna consulta o problema para acceder, contacta con soporte técnico.</p>

            <p>Saludos,<br>
            <strong>Sistema Lucy AMS</strong><br>
            Facultad de Ciencias Económicas<br>
            Universidad Nacional de Río Cuarto</p>
        </div>

        <div class="footer">
            <p>Este es un mensaje automático, por favor no responder.</p>
        </div>
    </div>
</body>
</html>
"""

        try:
            email_to = alumno.email_personal or alumno.email_institucional
            if not email_to:
                logger.error(f"Alumno {alumno.id} no tiene email configurado")
                return False

            logger.info(f"Enviando email de enrollamiento Moodle a {email_to}")

            result = send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=[email_to],
                html_message=html_message,
                fail_silently=False
            )

            if result == 1:
                logger.info(f"Email de enrollamiento Moodle enviado a {email_to}")
                log_to_db('SUCCESS', 'email_service', f'Email de enrollamiento Moodle enviado a {email_to}',
                         detalles={'email': email_to, 'courses': courses_enrolled}, alumno=alumno)
                return True
            else:
                logger.warning(f"send_mail retornó {result} para {email_to}")
                return False

        except Exception as e:
            logger.error(f"Error enviando email de enrollamiento a {alumno.email}: {e}")
            log_to_db('ERROR', 'email_service', f'Error enviando email de enrollamiento',
                     detalles={'error': str(e)}, alumno=alumno)
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
            # IMPORTANTE: Siempre enviar al email_personal
            email_destino = alumno.email_personal or alumno.email_institucional
            if not email_destino:
                logger.error(f"Alumno {alumno.id} no tiene email personal ni institucional")
                return False

            logger.info(f"Enviando confirmación de enrolamiento a {email_destino} (email personal)")

            result = send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=[email_destino],
                fail_silently=False
            )

            if result == 1:
                logger.info(f"Confirmación de enrolamiento enviada a {email_destino}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error enviando confirmación a {email_destino}: {e}")
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
