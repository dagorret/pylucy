"""
Management command para cargar plantillas de email por defecto.

Uso:
    python manage.py cargar_plantillas_email
    python manage.py cargar_plantillas_email --force  # Sobrescribe plantillas existentes
"""
from django.core.management.base import BaseCommand
from alumnos.models import Configuracion


class Command(BaseCommand):
    help = 'Carga las plantillas de email por defecto en la configuración del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescribe las plantillas existentes',
        )

    def handle(self, *args, **options):
        force = options['force']

        # Obtener configuración (Singleton)
        config = Configuracion.load()

        self.stdout.write(self.style.HTTP_INFO('🔧 Cargando plantillas de email por defecto...'))

        # ==============================================================================
        # PLANTILLA DE BIENVENIDA
        # ==============================================================================
        if not config.email_plantilla_bienvenida or force:
            config.email_asunto_bienvenida = "Bienvenido/a a la UNRC"
            config.email_plantilla_bienvenida = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #003366; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Bienvenido/a a la UNRC</h1>
        </div>
        <div class="content">
            <h2>Hola {nombre} {apellido},</h2>
            <p>Te damos la bienvenida a la <strong>Universidad Nacional de Río Cuarto</strong>.</p>
            <p>En breve recibirás un email con tus credenciales de acceso a los servicios institucionales.</p>
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
</html>"""
            self.stdout.write(self.style.SUCCESS('  ✅ Plantilla de bienvenida cargada'))
        else:
            self.stdout.write(self.style.WARNING('  ⏭️  Plantilla de bienvenida ya existe (usa --force para sobrescribir)'))

        # ==============================================================================
        # PLANTILLA DE CREDENCIALES
        # ==============================================================================
        if not config.email_plantilla_credenciales or force:
            config.email_asunto_credenciales = "Credenciales de acceso - UNRC"
            config.email_plantilla_credenciales = """<!DOCTYPE html>
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
            <h2>Hola {nombre} {apellido},</h2>
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
</html>"""
            self.stdout.write(self.style.SUCCESS('  ✅ Plantilla de credenciales cargada'))
        else:
            self.stdout.write(self.style.WARNING('  ⏭️  Plantilla de credenciales ya existe (usa --force para sobrescribir)'))

        # ==============================================================================
        # PLANTILLA DE RESETEO DE PASSWORD
        # ==============================================================================
        if not config.email_plantilla_password or force:
            config.email_asunto_password = "Nueva contraseña - UNRC"
            config.email_plantilla_password = """<!DOCTYPE html>
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
        .warning {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Nueva Contraseña - UNRC</h1>
        </div>
        <div class="content">
            <h2>Hola {nombre} {apellido},</h2>
            <p>Se ha generado una nueva contraseña temporal para tu cuenta institucional.</p>
            <div class="credentials">
                <p><strong>Usuario:</strong> {upn}</p>
                <p><strong>Nueva contraseña temporal:</strong> {password}</p>
            </div>
            <div class="warning">
                <strong>⚠️ IMPORTANTE:</strong>
                <ul>
                    <li>Al ingresar con esta contraseña, se te pedirá cambiarla</li>
                    <li>Guarda tu nueva contraseña en un lugar seguro</li>
                    <li>Si no solicitaste este cambio, contacta con soporte técnico inmediatamente</li>
                </ul>
            </div>
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
</html>"""
            self.stdout.write(self.style.SUCCESS('  ✅ Plantilla de password cargada'))
        else:
            self.stdout.write(self.style.WARNING('  ⏭️  Plantilla de password ya existe (usa --force para sobrescribir)'))

        # ==============================================================================
        # PLANTILLA DE ENROLLAMIENTO MOODLE
        # ==============================================================================
        if not config.email_plantilla_enrollamiento or force:
            config.email_asunto_enrollamiento = "Acceso al Ecosistema Virtual - UNRC"
            config.email_plantilla_enrollamiento = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #003366; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .info-box {{ background-color: #e8f4f8; padding: 15px; border-left: 4px solid #003366; margin: 20px 0; }}
        .credentials {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
        .credentials strong {{ color: #003366; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #003366; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }}
        .warning {{ background-color: #d1ecf1; padding: 10px; border-left: 4px solid #0c5460; margin: 15px 0; }}
        ul {{ padding-left: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Ecosistema Virtual UNRC</h1>
        </div>
        <div class="content">
            <h2>Hola {nombre} {apellido},</h2>
            <p>¡Bienvenido/a al <strong>Ecosistema Virtual</strong> de la Facultad de Ciencias Económicas!</p>
            <p>Has sido enrollado/a en nuestro campus virtual Moodle.</p>
            <div class="info-box">
                <h3>🌐 ACCESO AL ECOSISTEMA VIRTUAL:</h3>
                <p><strong>URL:</strong> <a href="{moodle_url}">{moodle_url}</a></p>
            </div>
            <div class="credentials">
                <h3>🔑 CREDENCIALES DE ACCESO:</h3>
                <p><strong>Usuario:</strong> {upn}</p>
                <p><strong>Contraseña:</strong> La misma que usas para Microsoft Teams</p>
            </div>
            <div class="warning">
                <strong>⚠️ IMPORTANTE:</strong>
                <ul>
                    <li>Usa las mismas credenciales que recibiste para Teams</li>
                    <li>Si cambiaste tu contraseña de Teams, usa la nueva contraseña</li>
                    <li>El acceso es mediante autenticación de Microsoft (OpenID Connect)</li>
                </ul>
            </div>
            <div class="info-box">
                <h3>📚 CURSOS ENROLLADOS:</h3>
                {cursos_html}
            </div>
            <p style="text-align: center;">
                <a href="{moodle_url}" class="button">Acceder al Ecosistema Virtual</a>
            </p>
            <p>Si tienes alguna consulta o problema para acceder, no dudes en contactar con soporte técnico.</p>
            <p>Saludos,<br>
            <strong>Sistema Lucy AMS</strong><br>
            Facultad de Ciencias Económicas<br>
            Universidad Nacional de Río Cuarto</p>
        </div>
        <div class="footer">
            Este es un mensaje automático, por favor no responder.<br>
            Universidad Nacional de Río Cuarto - Río Cuarto, Argentina
        </div>
    </div>
</body>
</html>"""
            self.stdout.write(self.style.SUCCESS('  ✅ Plantilla de enrollamiento cargada'))
        else:
            self.stdout.write(self.style.WARNING('  ⏭️  Plantilla de enrollamiento ya existe (usa --force para sobrescribir)'))

        # Guardar configuración
        config.save()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Proceso completado'))
        self.stdout.write(f'   - Email de bienvenida: {len(config.email_plantilla_bienvenida)} caracteres')
        self.stdout.write(f'   - Email de credenciales: {len(config.email_plantilla_credenciales)} caracteres')
        self.stdout.write(f'   - Email de password: {len(config.email_plantilla_password)} caracteres')
        self.stdout.write(f'   - Email de enrollamiento: {len(config.email_plantilla_enrollamiento)} caracteres')
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('💡 Tip: Puedes editar estas plantillas desde el admin de Django'))
        self.stdout.write(self.style.HTTP_INFO('    en Configuración del Sistema > Plantillas de Emails'))
