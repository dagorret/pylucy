#!/bin/bash
#
# Script para actualizar plantillas de email en la configuración de PyLucy
# Actualiza las plantillas HTML con las nuevas versiones que incluyen:
# - Credenciales de acceso (password)
# - Lista de cursos en HTML
# - Diseño profesional con CSS
#

set -e  # Salir si hay errores

echo "============================================"
echo "ACTUALIZACIÓN DE PLANTILLAS DE EMAIL"
echo "PyLucy - Sistema de Gestión de Alumnos"
echo "============================================"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Este script debe ejecutarse desde el directorio raíz del proyecto (donde está manage.py)"
    exit 1
fi

echo "📧 Actualizando plantillas de email en la base de datos..."
echo ""

# Ejecutar script Python para actualizar la configuración
python3 << 'PYTHON_SCRIPT'
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/carlos/work/pylucy/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pylucy.settings')
django.setup()

from alumnos.models import Configuracion

# Cargar configuración
config = Configuracion.load()

print("📝 Configuración actual:")
print(f"   - Asunto bienvenida: {config.email_asunto_bienvenida or '(no configurado)'}")
print(f"   - Asunto enrollamiento: {config.email_asunto_enrollamiento or '(no configurado)'}")
print(f"   - Plantilla bienvenida: {'✓ Configurada' if config.email_plantilla_bienvenida else '✗ No configurada'}")
print(f"   - Plantilla enrollamiento: {'✓ Configurada' if config.email_plantilla_enrollamiento else '✗ No configurada'}")
print()

# ============================================
# PLANTILLA HTML DE ENROLLAMIENTO (MOODLE)
# ============================================

plantilla_enrollamiento_html = """<!DOCTYPE html>
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
        li {{ margin: 8px 0; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        h1 {{ margin: 0; font-size: 24px; }}
        h3 {{ color: #003366; margin-top: 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Ecosistema Virtual FCE - UNRC</h1>
        </div>

        <div class="content">
            <p>Hola <strong>{nombre} {apellido}</strong>,</p>

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
</html>"""

# ============================================
# ACTUALIZAR CONFIGURACIÓN
# ============================================

print("💾 Actualizando plantillas en la base de datos...")
print()

# Actualizar asuntos si no están configurados
if not config.email_asunto_bienvenida:
    config.email_asunto_bienvenida = "Bienvenido/a a la UNRC - {nombre} {apellido}"
    print("✓ Asunto de bienvenida actualizado")

if not config.email_asunto_enrollamiento:
    config.email_asunto_enrollamiento = "Acceso al Ecosistema Virtual - UNRC"
    print("✓ Asunto de enrollamiento actualizado")

# Actualizar plantilla de enrollamiento (siempre)
config.email_plantilla_enrollamiento = plantilla_enrollamiento_html
print("✓ Plantilla HTML de enrollamiento actualizada")

# Guardar cambios
config.save()

print()
print("=" * 60)
print("✅ PLANTILLAS ACTUALIZADAS EXITOSAMENTE")
print("=" * 60)
print()
print("📋 Variables disponibles en las plantillas:")
print()
print("   Plantilla de enrollamiento:")
print("   - {nombre}         : Nombre del alumno")
print("   - {apellido}       : Apellido del alumno")
print("   - {upn}            : Email institucional (usuario)")
print("   - {password}       : Contraseña generada")
print("   - {moodle_url}     : URL del campus virtual")
print("   - {cursos_html}    : Lista de cursos en HTML (<ul><li>...)")
print("   - {cursos_texto}   : Lista de cursos en texto plano")
print()
print("   Plantilla de bienvenida:")
print("   - {nombre}         : Nombre del alumno")
print("   - {apellido}       : Apellido del alumno")
print("   - {dni}            : DNI del alumno")
print("   - {email}          : Email del alumno")
print()
print("💡 Puedes editar estas plantillas desde el admin de Django:")
print("   Admin → Alumnos → Configuración → Emails")
print()

PYTHON_SCRIPT

echo ""
echo "============================================"
echo "✅ PROCESO COMPLETADO"
echo "============================================"
echo ""
echo "Los cambios ya están en la base de datos."
echo "Puedes verificarlos en el admin de Django."
echo ""
