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
        html_message = None  # Inicializar siempre
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
                html_message = None  # Resetear si hubo error

        if not plantilla:
            # Fallback: Plantilla FCE - UNRC (Credenciales)
            message = f"Hola {alumno.nombre} {alumno.apellido}, tus credenciales de acceso V.ECO están disponibles."
            html_message = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Bienvenida - V.ECO</title>
  <style>
    body {{ margin: 0; padding: 0; background: #f4f6f9; font-family: Arial, sans-serif; line-height: 1.6; color: #1f2937; }}
    .wrapper {{ width: 100%; background: #f4f6f9; padding: 24px 12px; }}
    .container {{ max-width: 640px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e5e7eb; }}
    .header {{ background: #0b2f5b; padding: 26px 20px; text-align: center; color: #fff; }}
    .header h1 {{ margin: 0; font-size: 20px; letter-spacing: 0.2px; }}
    .header p {{ margin: 6px 0 0; font-size: 13px; opacity: 0.9; }}
    .content {{ padding: 22px 20px; }}
    .title {{ margin: 0 0 10px; font-size: 18px; }}
    .muted {{ color: #6b7280; font-size: 13px; margin: 0 0 14px; }}
    .card {{ background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px 14px; margin: 16px 0; }}
    .label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: .6px; margin: 0 0 4px; }}
    .value {{ margin: 0; font-size: 15px; color: #111827; }}
    .pill {{ display: inline-block; font-size: 12px; padding: 4px 10px; border-radius: 999px; background: #e8f1ff; color: #0b2f5b; border: 1px solid #cfe1ff; margin-bottom: 10px; }}
    .warning {{ background: #fff7e6; border: 1px solid #ffe1a6; border-left: 5px solid #f59e0b; border-radius: 10px; padding: 12px 14px; margin: 16px 0; }}
    .warning strong {{ color: #92400e; }}
    .warning ul {{ margin: 8px 0 0 18px; padding: 0; }}
    .steps {{ margin: 12px 0 0; padding-left: 18px; }}
    .btn-wrap {{ text-align: center; margin: 18px 0 8px; }}
    .button {{ display: inline-block; background: #0b2f5b; color: #ffffff !important; text-decoration: none; padding: 12px 18px; border-radius: 10px; font-weight: bold; font-size: 14px; }}
    .help {{ margin-top: 16px; font-size: 13px; color: #374151; }}
    .help b {{ color: #0b2f5b; }}
    .divider {{ height: 1px; background: #e5e7eb; margin: 18px 0; }}
    .signature {{ font-size: 13px; color: #374151; }}
    .footer {{ padding: 16px 20px; background: #fbfbfb; text-align: center; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; }}
    a {{ color: #0b2f5b; }}
  </style>
</head>

<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <h1>Credenciales de acceso | V.ECO (FCE)</h1>
        <p>Universidad Nacional de Río Cuarto</p>
      </div>

      <div class="content">
        <span class="pill">Bienvenida/o al ecosistema virtual</span>

        <h2 class="title">Hola {alumno.nombre} {alumno.apellido},</h2>
        <p class="muted">
          Te compartimos tu cuenta institucional para ingresar al <b>Ecosistema Virtual de la FCE (V.ECO)</b>.
        </p>

        <div class="card">
          <p class="label">Usuario</p>
          <p class="value"><b>{upn}</b></p>

          <div class="divider"></div>

          <p class="label">Contraseña temporal</p>
          <p class="value"><b>{password}</b></p>
        </div>

        <div class="warning">
          <strong>⚠️ Importante</strong>
          <ul>
            <li>En tu primer ingreso, el sistema te solicitará <b>cambiar la contraseña</b>.</li>
            <li>Guardá tu nueva contraseña en un lugar seguro y no la compartas.</li>
          </ul>
        </div>

        <p class="muted" style="margin-bottom:8px;">
          Para ingresar, seguí estos pasos:
        </p>
        <ol class="steps">
          <li>Accedé a <b>V.ECO</b> desde el botón de abajo.</li>
          <li>Ingresá y seleccioná el botón <b>MS TEAMS</b> de la FCE.</li>
          <li>Si es tu primera vez, completá el cambio de contraseña.</li>
        </ol>

        <div class="btn-wrap">
          <a class="button" href="https://v.eco.unrc.edu.ar" target="_blank" rel="noopener">Accedé a V.ECO</a>
        </div>

        <p class="help">
          Ante cualquier consulta, escribinos a: <b>v.estudiantes@fce.unrc.edu.ar</b><br />
          Tel.: <b>0358 4676542</b><br />
          También podés consultar al <b>ChatBOT FCE</b> las 24 hs.
        </p>

        <div class="divider"></div>

        <p class="signature">
          Atentamente,<br />
          Secretaría de Virtualización Estratégica<br />
          Facultad de Ciencias Económicas<br />
          Universidad Nacional de Río Cuarto
        </p>
      </div>

      <div class="footer">
        Este es un mensaje automático, por favor no responder.
      </div>
    </div>
  </div>
</body>
</html>"""
        else:
            # Si hay plantilla personalizada pero no es HTML, crear versión texto simple
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
                html_message = None  # Resetear si hubo error

        if not plantilla:
            # Fallback: Plantilla FCE - UNRC
            message = f"Hola {alumno.apellido}, {alumno.nombre}, bienvenido/a a la FCE-UNRC."
            html_message = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Bienvenida | FCE - UNRC</title>
  <style>
    body {{ margin: 0; padding: 0; background: #f4f6f9; font-family: Arial, sans-serif; line-height: 1.6; color: #1f2937; }}
    .wrapper {{ width: 100%; background: #f4f6f9; padding: 24px 12px; }}
    .container {{ max-width: 640px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e5e7eb; }}
    .header {{ background: #0b2f5b; padding: 26px 20px; text-align: center; color: #fff; }}
    .header h1 {{ margin: 0; font-size: 20px; letter-spacing: 0.2px; }}
    .header p {{ margin: 6px 0 0; font-size: 13px; opacity: 0.9; }}
    .content {{ padding: 22px 20px; }}
    .pill {{ display: inline-block; font-size: 12px; padding: 4px 10px; border-radius: 999px; background: #e8f1ff; color: #0b2f5b; border: 1px solid #cfe1ff; margin-bottom: 10px; }}
    .title {{ margin: 0 0 10px; font-size: 18px; }}
    .muted {{ color: #6b7280; font-size: 13px; margin: 0 0 14px; }}
    .card {{ background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px 14px; margin: 16px 0; }}
    .label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: .6px; margin: 0 0 6px; }}
    .list {{ margin: 8px 0 0 18px; padding: 0; }}
    .btn-wrap {{ text-align: center; margin: 18px 0 8px; }}
    .button {{ display: inline-block; background: #0b2f5b; color: #ffffff !important; text-decoration: none; padding: 12px 18px; border-radius: 10px; font-weight: bold; font-size: 14px; }}
    .divider {{ height: 1px; background: #e5e7eb; margin: 18px 0; }}
    .footer {{ padding: 16px 20px; background: #fbfbfb; text-align: center; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; }}
    a {{ color: #0b2f5b; }}
  </style>
</head>

<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <h1>Bienvenida/o a la Facultad de Ciencias Económicas</h1>
        <p>Universidad Nacional de Río Cuarto</p>
      </div>

      <div class="content">
        <span class="pill">Inscripción recibida</span>

        <h2 class="title">Estimado/a {alumno.apellido}, {alumno.nombre} <span style="font-weight: normal; color:#6b7280;">(DNI: {alumno.dni})</span></h2>

        <p class="muted">
          Es un placer darte la bienvenida a la <b>Facultad de Ciencias Económicas de la UNRC</b>.
          Hemos recibido tu inscripción correctamente.
        </p>

        <div class="card">
          <p class="label">En los próximos días vas a recibir información sobre</p>
          <ul class="list">
            <li><b>Credenciales de acceso a V.ECO</b></li>
          </ul>

          <div class="divider" style="margin: 14px 0;"></div>

          <p class="muted" style="margin:0;">
            Para ver información y materiales del cursillo de ingreso, ingresá desde el siguiente enlace:
          </p>

          <div class="btn-wrap" style="margin-top:12px;">
            <a class="button" href="https://www.eco.unrc.edu.ar/ingresantes/" target="_blank" rel="noopener">
              Ir a Ingresantes
            </a>
          </div>

          <p class="muted" style="margin:10px 0 0;">
            Si el botón no funciona, copiá y pegá este enlace en tu navegador:<br />
            <a href="https://www.eco.unrc.edu.ar/ingresantes/" target="_blank" rel="noopener">https://www.eco.unrc.edu.ar/ingresantes/</a>
          </p>
        </div>

        <p style="margin: 0;">
          ¡Bienvenido/a y éxitos en esta nueva etapa!
        </p>
      </div>

      <div class="footer">
        <b>Secretaría de Virtualización Estratégica - Facultad de Ciencias Económicas – UNRC</b><br />
        Ruta Nacional 36 Km 601 – Río Cuarto, Córdoba<br />
        <a href="https://www.eco.unrc.edu.ar" target="_blank" rel="noopener">www.eco.unrc.edu.ar</a>
      </div>
    </div>
  </div>
</body>
</html>"""
        else:
            # Si hay plantilla personalizada pero no es HTML, no enviar html
            if not html_message:
                html_message = None

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
            # Fallback: Plantilla FCE - UNRC (Enrollamiento)
            message = f"Hola {alumno.nombre} {alumno.apellido}, ya tienes acceso al Campus Virtual Moodle."
            html_message = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Ecosistema Virtual FCE - V.ECO</title>
  <style>
    body {{ margin: 0; padding: 0; background: #f4f6f9; font-family: Arial, sans-serif; line-height: 1.6; color: #1f2937; }}
    .wrapper {{ width: 100%; background: #f4f6f9; padding: 24px 12px; }}
    .container {{ max-width: 640px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e5e7eb; }}
    .header {{ background: #0b2f5b; padding: 26px 20px; text-align: center; color: #fff; }}
    .header h1 {{ margin: 0; font-size: 20px; letter-spacing: 0.2px; }}
    .header p {{ margin: 6px 0 0; font-size: 13px; opacity: 0.9; }}
    .content {{ padding: 22px 20px; }}
    .pill {{ display: inline-block; font-size: 12px; padding: 4px 10px; border-radius: 999px; background: #e8f1ff; color: #0b2f5b; border: 1px solid #cfe1ff; margin-bottom: 10px; }}
    .title {{ margin: 0 0 10px; font-size: 18px; }}
    .muted {{ color: #6b7280; font-size: 13px; margin: 0 0 14px; }}
    .card {{ background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px 14px; margin: 16px 0; }}
    .label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: .6px; margin: 0 0 8px; }}
    .divider {{ height: 1px; background: #e5e7eb; margin: 14px 0; }}
    .button {{ display: inline-block; background: #0b2f5b; color: #ffffff !important; text-decoration: none; padding: 12px 18px; border-radius: 10px; font-weight: bold; font-size: 14px; }}
    .btn-wrap {{ text-align: center; margin: 14px 0 6px; }}
    .notice {{ background: #fff7e6; border: 1px solid #ffe1a6; border-left: 5px solid #f59e0b; border-radius: 10px; padding: 12px 14px; margin: 16px 0; }}
    .notice strong {{ color: #92400e; }}
    .footer {{ padding: 16px 20px; background: #fbfbfb; text-align: center; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; }}
    a {{ color: #0b2f5b; }}
  </style>
</head>

<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <h1>Ecosistema Virtual FCE - V.ECO</h1>
        <p>Facultad de Ciencias Económicas · UNRC</p>
      </div>

      <div class="content">
        <span class="pill">Cursillo de ingreso</span>

        <h2 class="title">Hola {alumno.nombre} {alumno.apellido},</h2>

        <p class="muted">
          ¡Bienvenido/a al <b>Ecosistema Virtual</b> de la Facultad de Ciencias Económicas (<b>V.ECO</b>)!
          Has sido matriculado/a a los siguientes módulos del cursillo de ingreso:
        </p>

        <div class="card">
          <p class="label">Módulos matriculados</p>
          {cursos_html}
        </div>

        <div class="card">
          <p class="label">🌐 Acceso al ecosistema virtual</p>

          <p style="margin:0; font-size: 14px;">
            URL: <a href="{moodle_url}" target="_blank" rel="noopener">{moodle_url}</a>
          </p>

          <div class="divider"></div>

          <p class="muted" style="margin:0;">
            🔑 Ingresá con el <b>nombre de usuario</b> y la <b>contraseña</b> que recibiste en el correo anterior.
            Guardá estas credenciales en un lugar seguro.
          </p>

          <div class="btn-wrap">
            <a class="button" href="{moodle_url}" target="_blank" rel="noopener">Ingresar a V.ECO</a>
          </div>

          <p class="muted" style="margin:8px 0 0;">
            Si el botón no funciona, copiá y pegá este enlace en tu navegador:<br />
            <a href="{moodle_url}" target="_blank" rel="noopener">{moodle_url}</a>
          </p>
        </div>

        <div class="notice">
          <strong>📩 Soporte</strong><br />
          Si tenés alguna consulta, escribinos a
          <b><a href="mailto:v.estudiantes@fce.unrc.edu.ar">v.estudiantes@fce.unrc.edu.ar</a></b>
          o consultá el <b>CHATBOT</b> de la FCE desde la página de la Facultad (24 hs).
        </div>
      </div>

      <div class="footer">
        Este es un mensaje automático, por favor no responder.<br />
        <b>Facultad de Ciencias Económicas – UNRC</b>
      </div>
    </div>
  </div>
</body>
</html>"""
        else:
            # Si hay plantilla personalizada pero no es HTML, no enviar html
            if not html_message:
                html_message = None

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

    def enviar_email_password_reset(self, alumno, password: str) -> bool:
        """
        Envía email con nueva contraseña temporal después de un reset.

        Args:
            alumno: Instancia del modelo Alumno
            password: Nueva contraseña temporal

        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        from ..models import Configuracion
        config = Configuracion.load()

        upn = alumno.email_institucional or f"{alumno.dni}@eco.unrc.edu.ar"
        subject = "Nueva contraseña temporal - FCE UNRC"

        message = f"Hola {alumno.nombre} {alumno.apellido}, se ha generado una nueva contraseña temporal."
        html_message = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Nueva contraseña temporal | FCE - UNRC</title>
  <style>
    body {{ margin: 0; padding: 0; background: #f4f6f9; font-family: Arial, sans-serif; line-height: 1.6; color: #1f2937; }}
    .wrapper {{ width: 100%; background: #f4f6f9; padding: 24px 12px; }}
    .container {{ max-width: 640px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e5e7eb; }}
    .header {{ background: #0b2f5b; padding: 26px 20px; text-align: center; color: #fff; }}
    .header h1 {{ margin: 0; font-size: 20px; letter-spacing: 0.2px; }}
    .header p {{ margin: 6px 0 0; font-size: 13px; opacity: 0.9; }}
    .content {{ padding: 22px 20px; }}
    .pill {{ display: inline-block; font-size: 12px; padding: 4px 10px; border-radius: 999px; background: #e8f1ff; color: #0b2f5b; border: 1px solid #cfe1ff; margin-bottom: 10px; }}
    .title {{ margin: 0 0 10px; font-size: 18px; }}
    .muted {{ color: #6b7280; font-size: 13px; margin: 0 0 14px; }}
    .card {{ background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px 14px; margin: 16px 0; }}
    .label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: .6px; margin: 0 0 6px; }}
    .value {{ margin: 0; font-size: 15px; color: #111827; }}
    .divider {{ height: 1px; background: #e5e7eb; margin: 14px 0; }}
    .warning {{ background: #fff7e6; border: 1px solid #ffe1a6; border-left: 5px solid #f59e0b; border-radius: 10px; padding: 12px 14px; margin: 16px 0; }}
    .warning strong {{ color: #92400e; }}
    .warning ul {{ margin: 8px 0 0 18px; padding: 0; }}
    .help {{ margin-top: 16px; font-size: 13px; color: #374151; }}
    .help b {{ color: #0b2f5b; }}
    .footer {{ padding: 16px 20px; background: #fbfbfb; text-align: center; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; }}
    a {{ color: #0b2f5b; }}
  </style>
</head>

<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <h1>Nueva contraseña temporal</h1>
        <p>Facultad de Ciencias Económicas · UNRC</p>
      </div>

      <div class="content">
        <span class="pill">Recuperación de acceso</span>

        <h2 class="title">Hola {alumno.nombre} {alumno.apellido},</h2>

        <p class="muted">
          Se ha generado una <b>nueva contraseña temporal</b> para tu cuenta institucional.
          Utilizala para ingresar y completar el cambio de contraseña.
        </p>

        <div class="card">
          <p class="label">Usuario</p>
          <p class="value"><b>{upn}</b></p>

          <div class="divider"></div>

          <p class="label">Nueva contraseña temporal</p>
          <p class="value"><b>{password}</b></p>
        </div>

        <div class="warning">
          <strong>⚠️ Importante</strong>
          <ul>
            <li>Al ingresar con esta contraseña, el sistema te solicitará <b>cambiarla</b>.</li>
            <li>Guardá tu nueva contraseña en un lugar seguro y no la compartas.</li>
            <li>Si no solicitaste este cambio, contactate con soporte técnico <b>de inmediato</b>.</li>
          </ul>
        </div>

        <p class="help">
          Ante cualquier consulta, escribinos a: <b><a href="mailto:v.estudiantes@fce.unrc.edu.ar">v.estudiantes@fce.unrc.edu.ar</a></b>
        </p>

        <p class="help" style="margin-top: 12px;">
          Saludos,<br />
          <b>Facultad de Ciencias Económicas</b><br />
          Universidad Nacional de Río Cuarto
        </p>
      </div>

      <div class="footer">
        Este es un mensaje automático, por favor no responder.<br />
        <b>Facultad de Ciencias Económicas – UNRC</b>
      </div>
    </div>
  </div>
</body>
</html>"""

        try:
            email_destino = alumno.email_personal or alumno.email_institucional
            if not email_destino:
                logger.error(f"Alumno {alumno.id} no tiene email configurado")
                return False

            logger.info(f"Enviando email de password reset a {email_destino}")

            result = send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=[email_destino],
                html_message=html_message,
                fail_silently=False
            )

            if result == 1:
                logger.info(f"Email de password reset enviado a {email_destino}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error enviando email de password reset a {email_destino}: {e}")
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
