"""
Migración de datos para poblar la configuración inicial del sistema.
Incluye credenciales de Azure, Moodle, SIAL/UTI, y plantillas de emails.
"""

from django.db import migrations


def populate_configuracion(apps, schema_editor):
    """Carga la configuración inicial del sistema."""
    Configuracion = apps.get_model('alumnos', 'Configuracion')

    # Eliminar configuraciones anteriores si existen
    Configuracion.objects.all().delete()

    # Crear configuración única
    Configuracion.objects.create(
        # ========================================
        # Procesamiento y Rate Limiting
        # ========================================
        batch_size=20,
        rate_limit_teams=10,
        rate_limit_moodle=30,

        # ========================================
        # Credenciales Teams/Azure AD
        # ========================================
        teams_tenant_id='f69f5e9f-9083-483f-a813-8c5172ba159b',
        teams_client_id='15e37c15-4ec5-481c-916c-14ae7c4bf9c4',
        teams_client_secret='zPz8Q~jfDTZ6xWiP62h5IH3JZNBCQMTmUJX0Jb8w',
        account_prefix='test-a',  # 'a' para producción, 'test-a' para testing

        # ========================================
        # API SIAL/UTI
        # ========================================
        sial_base_url='http://mock-api-uti:8000',  # Cambiar a https://sial.unrc.edu.ar en producción
        sial_basic_user='usuario',
        sial_basic_pass='contrasena',

        # ========================================
        # Moodle
        # ========================================
        moodle_base_url='https://v.eco.unrc.edu.ar',
        moodle_wstoken='45fba879dcddc17a16436ac156cb880e',
        moodle_email_type='institucional',
        moodle_student_roleid=5,
        moodle_auth_method='oauth2',

        # ========================================
        # Plantillas de Emails
        # ========================================
        email_plantilla_bienvenida="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #0066cc; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>¡Bienvenido/a a la Facultad de Ciencias Económicas!</h1>
        </div>
        <div class="content">
            <p>Estimado/a <strong>{apellido}, {nombre}</strong> (DNI: {dni}):</p>

            <p>Es un placer darte la bienvenida a la <strong>Facultad de Ciencias Económicas de la UNRC</strong>.</p>

            <p>Hemos recibido tu inscripción correctamente. En los próximos días recibirás información sobre:</p>
            <ul>
                <li>Credenciales de acceso a Microsoft Teams</li>
                <li>Acceso al campus virtual (Moodle)</li>
                <li>Información sobre el curso de ingreso</li>
                <li>Calendario académico</li>
            </ul>

            <p>Cualquier consulta, no dudes en contactarnos a: <a href="mailto:economia@eco.unrc.edu.ar">economia@eco.unrc.edu.ar</a></p>

            <p>¡Bienvenido/a y éxitos en esta nueva etapa!</p>
        </div>
        <div class="footer">
            <p>Facultad de Ciencias Económicas - UNRC<br>
            Ruta Nacional 36 Km 601 - Río Cuarto, Córdoba<br>
            <a href="https://eco.unrc.edu.ar">www.eco.unrc.edu.ar</a></p>
        </div>
    </div>
</body>
</html>
""",

        email_plantilla_credenciales="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .credentials {{ background-color: white; padding: 15px; margin: 20px 0; border-left: 4px solid #28a745; }}
        .credentials strong {{ color: #28a745; }}
        .warning {{ background-color: #fff3cd; padding: 10px; margin: 15px 0; border-left: 4px solid #ffc107; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Credenciales de Acceso - Microsoft Teams</h1>
        </div>
        <div class="content">
            <p>Estimado/a <strong>{apellido}, {nombre}</strong>:</p>

            <p>Tu cuenta de <strong>Microsoft Teams</strong> ha sido creada exitosamente. A continuación encontrarás tus credenciales de acceso:</p>

            <div class="credentials">
                <p><strong>Usuario (UPN):</strong> {upn}</p>
                <p><strong>Contraseña temporal:</strong> {password}</p>
            </div>

            <div class="warning">
                <p><strong>⚠️ IMPORTANTE:</strong></p>
                <ul>
                    <li>Esta es una contraseña <strong>temporal</strong></li>
                    <li>Se te pedirá cambiarla en tu primer inicio de sesión</li>
                    <li>Guarda bien tu nueva contraseña</li>
                    <li>No compartas tus credenciales con nadie</li>
                </ul>
            </div>

            <h3>¿Cómo acceder?</h3>
            <ol>
                <li>Ingresa a <a href="https://teams.microsoft.com">teams.microsoft.com</a></li>
                <li>Usa tu usuario (UPN) y contraseña temporal</li>
                <li>Sigue las instrucciones para cambiar tu contraseña</li>
                <li>¡Listo! Ya podés acceder a tus clases y materiales</li>
            </ol>

            <p>También podés descargar la aplicación de Teams para escritorio o móvil desde:</p>
            <p><a href="https://www.microsoft.com/es-ar/microsoft-teams/download-app">Descargar Microsoft Teams</a></p>

            <p>Cualquier problema con tu acceso, contactanos a: <a href="mailto:soporte@eco.unrc.edu.ar">soporte@eco.unrc.edu.ar</a></p>
        </div>
        <div class="footer">
            <p>Facultad de Ciencias Económicas - UNRC<br>
            Ruta Nacional 36 Km 601 - Río Cuarto, Córdoba<br>
            <a href="https://eco.unrc.edu.ar">www.eco.unrc.edu.ar</a></p>
        </div>
    </div>
</body>
</html>
""",

        email_plantilla_password="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #ffc107; color: #333; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .credentials {{ background-color: white; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107; }}
        .credentials strong {{ color: #ffc107; }}
        .warning {{ background-color: #f8d7da; padding: 10px; margin: 15px 0; border-left: 4px solid #dc3545; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Reseteo de Contraseña - Microsoft Teams</h1>
        </div>
        <div class="content">
            <p>Estimado/a <strong>{apellido}, {nombre}</strong>:</p>

            <p>Tu contraseña de <strong>Microsoft Teams</strong> ha sido reseteada.</p>

            <div class="credentials">
                <p><strong>Usuario (UPN):</strong> {upn}</p>
                <p><strong>Nueva contraseña temporal:</strong> {password}</p>
            </div>

            <div class="warning">
                <p><strong>⚠️ ATENCIÓN:</strong></p>
                <ul>
                    <li>Esta contraseña <strong>reemplaza</strong> tu contraseña anterior</li>
                    <li>Es una contraseña <strong>temporal</strong></li>
                    <li>Deberás cambiarla en tu próximo inicio de sesión</li>
                    <li>Si no solicitaste este cambio, contacta inmediatamente a soporte</li>
                </ul>
            </div>

            <h3>Pasos para acceder:</h3>
            <ol>
                <li>Ve a <a href="https://teams.microsoft.com">teams.microsoft.com</a></li>
                <li>Ingresa con tu usuario y la nueva contraseña temporal</li>
                <li>Cambia tu contraseña cuando se te solicite</li>
            </ol>

            <p>Si tenés problemas para acceder, escribinos a: <a href="mailto:soporte@eco.unrc.edu.ar">soporte@eco.unrc.edu.ar</a></p>
        </div>
        <div class="footer">
            <p>Facultad de Ciencias Económicas - UNRC<br>
            Ruta Nacional 36 Km 601 - Río Cuarto, Córdoba<br>
            <a href="https://eco.unrc.edu.ar">www.eco.unrc.edu.ar</a></p>
        </div>
    </div>
</body>
</html>
""",

        # ========================================
        # Configuración Email SMTP
        # ========================================
        email_from='no-reply@eco.unrc.edu.ar',
        email_host='mailhog',
        email_port=1025,
        email_use_tls=False,
    )


def reverse_configuracion(apps, schema_editor):
    """Elimina la configuración al hacer rollback."""
    Configuracion = apps.get_model('alumnos', 'Configuracion')
    Configuracion.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('alumnos', '0015_add_email_templates_and_auth'),
    ]

    operations = [
        migrations.RunPython(populate_configuracion, reverse_configuracion),
    ]
