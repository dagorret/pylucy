"""
Nombre del Módulo: 0016_populate_configuracion.py

Descripción:
Migración de base de datos generada por Django.

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


from django.db import migrations


def populate_configuracion(apps, schema_editor):
    """
    Carga la configuración inicial del sistema.
    Intenta cargar credenciales desde archivos JSON, si no usa valores por defecto.
    """
    import json
    import os
    from pathlib import Path

    Configuracion = apps.get_model('alumnos', 'Configuracion')

    # Eliminar configuraciones anteriores si existen
    Configuracion.objects.all().delete()

    # Intentar cargar credenciales desde archivos JSON
    credentials_dir = Path('/credenciales')

    # Función auxiliar para cargar JSON
    def load_creds(filename):
        filepath = credentials_dir / filename
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None

    # Cargar credenciales desde JSON o usar defaults
    uti_creds = load_creds('uti_credentials.json')
    moodle_creds = load_creds('moodle_credentials.json')
    teams_creds = load_creds('teams_credentials.json')

    # Valores UTI
    sial_url = uti_creds.get('base_url', 'http://mock-api-uti:8000') if uti_creds else 'http://mock-api-uti:8000'
    sial_user = uti_creds.get('basic_auth', {}).get('username', 'usuario') if uti_creds else 'usuario'
    sial_pass = uti_creds.get('basic_auth', {}).get('password', 'contrasena') if uti_creds else 'contrasena'

    # Valores Moodle
    moodle_url = moodle_creds.get('base_url', 'https://v.eco.unrc.edu.ar') if moodle_creds else 'https://v.eco.unrc.edu.ar'
    moodle_token = moodle_creds.get('wstoken', 'YOUR-TOKEN-HERE') if moodle_creds else 'YOUR-TOKEN-HERE'

    # Valores Teams
    teams_tenant = teams_creds.get('tenant_id', 'YOUR-TENANT-ID') if teams_creds else 'YOUR-TENANT-ID'
    teams_client = teams_creds.get('client_id', 'YOUR-CLIENT-ID') if teams_creds else 'YOUR-CLIENT-ID'
    teams_secret = teams_creds.get('client_secret', 'YOUR-SECRET') if teams_creds else 'YOUR-SECRET'

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
        teams_tenant_id=teams_tenant,
        teams_client_id=teams_client,
        teams_client_secret=teams_secret,
        account_prefix='test-a',  # 'a' para producción, 'test-a' para testing

        # ========================================
        # API SIAL/UTI
        # ========================================
        sial_base_url=sial_url,
        sial_basic_user=sial_user,
        sial_basic_pass=sial_pass,

        # ========================================
        # Moodle
        # ========================================
        moodle_base_url=moodle_url,
        moodle_wstoken=moodle_token,
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
