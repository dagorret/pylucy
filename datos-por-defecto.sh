#!/bin/bash
# ==============================================================================
# Script de Datos por Defecto para PyLucy
# ==============================================================================
# Este script carga las plantillas de email y configuraciones por defecto
# en la base de datos de PyLucy.
#
# Uso: ./datos-por-defecto.sh
#
# IMPORTANTE: Este script debe ejecutarse desde el contenedor de Django
# o con acceso a manage.py
# ==============================================================================

set -e  # Salir si hay algún error

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# ==============================================================================
# Función para cargar plantillas de email
# ==============================================================================
cargar_plantillas_email() {
    log_info "Cargando plantillas de email por defecto..."

    # Crear script Python temporal para cargar las plantillas
    cat > /tmp/cargar_plantillas.py << 'PYTHON_SCRIPT'
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pylucy.settings')
django.setup()

from alumnos.models import Configuracion

# Obtener configuración (Singleton)
config = Configuracion.load()

# ==============================================================================
# PLANTILLA DE BIENVENIDA
# ==============================================================================
config.email_asunto_bienvenida = "Bienvenido/a a la UNRC"
config.email_plantilla_bienvenida = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{{{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}}}
        .container {{{{ max-width: 600px; margin: 0 auto; padding: 20px; }}}}
        .header {{{{ background-color: #003366; color: white; padding: 20px; text-align: center; }}}}
        .content {{{{ padding: 20px; background-color: #f9f9f9; }}}}
        .footer {{{{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}}}
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

# ==============================================================================
# PLANTILLA DE CREDENCIALES
# ==============================================================================
config.email_asunto_credenciales = "Credenciales de acceso - UNRC"
config.email_plantilla_credenciales = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{{{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}}}
        .container {{{{ max-width: 600px; margin: 0 auto; padding: 20px; }}}}
        .header {{{{ background-color: #003366; color: white; padding: 20px; text-align: center; }}}}
        .content {{{{ padding: 20px; background-color: #f9f9f9; }}}}
        .credentials {{{{ background-color: #e8f4f8; padding: 15px; border-left: 4px solid #003366; margin: 20px 0; }}}}
        .credentials strong {{{{ color: #003366; }}}}
        .footer {{{{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}}}
        .button {{{{ display: inline-block; padding: 12px 24px; background-color: #003366; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }}}}
        .warning {{{{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 15px 0; }}}}
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

# ==============================================================================
# PLANTILLA DE RESETEO DE PASSWORD
# ==============================================================================
config.email_asunto_password = "Nueva contraseña - UNRC"
config.email_plantilla_password = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{{{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}}}
        .container {{{{ max-width: 600px; margin: 0 auto; padding: 20px; }}}}
        .header {{{{ background-color: #003366; color: white; padding: 20px; text-align: center; }}}}
        .content {{{{ padding: 20px; background-color: #f9f9f9; }}}}
        .credentials {{{{ background-color: #e8f4f8; padding: 15px; border-left: 4px solid #003366; margin: 20px 0; }}}}
        .credentials strong {{{{ color: #003366; }}}}
        .footer {{{{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}}}
        .warning {{{{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 15px 0; }}}}
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

# ==============================================================================
# PLANTILLA DE ENROLLAMIENTO MOODLE
# ==============================================================================
config.email_asunto_enrollamiento = "Acceso al Ecosistema Virtual - UNRC"
config.email_plantilla_enrollamiento = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{{{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}}}
        .container {{{{ max-width: 600px; margin: 0 auto; padding: 20px; }}}}
        .header {{{{ background-color: #003366; color: white; padding: 20px; text-align: center; }}}}
        .content {{{{ padding: 20px; background-color: #f9f9f9; }}}}
        .info-box {{{{ background-color: #e8f4f8; padding: 15px; border-left: 4px solid #003366; margin: 20px 0; }}}}
        .credentials {{{{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}}}
        .credentials strong {{{{ color: #003366; }}}}
        .footer {{{{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}}}
        .button {{{{ display: inline-block; padding: 12px 24px; background-color: #003366; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }}}}
        .warning {{{{ background-color: #d1ecf1; padding: 10px; border-left: 4px solid #0c5460; margin: 15px 0; }}}}
        ul {{{{ padding-left: 20px; }}}}
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

# Guardar configuración
config.save()

print("✅ Plantillas de email cargadas exitosamente")
print(f"   - Email de bienvenida: {len(config.email_plantilla_bienvenida)} caracteres")
print(f"   - Email de credenciales: {len(config.email_plantilla_credenciales)} caracteres")
print(f"   - Email de password: {len(config.email_plantilla_password)} caracteres")
print(f"   - Email de enrollamiento: {len(config.email_plantilla_enrollamiento)} caracteres")

PYTHON_SCRIPT

    # Ejecutar el script Python
    python /tmp/cargar_plantillas.py

    # Limpiar archivo temporal
    rm -f /tmp/cargar_plantillas.py

    log_success "Plantillas de email cargadas correctamente"
}

# ==============================================================================
# Función para exportar datos desde servidor de testing
# ==============================================================================
exportar_datos_testing() {
    log_info "Para exportar datos desde el servidor de testing, ejecuta:"
    echo ""
    echo "  docker exec pylucy-web python manage.py dumpdata alumnos.Configuracion --indent 2 > configuracion_backup.json"
    echo ""
    log_info "Luego importa con:"
    echo ""
    echo "  docker exec -i pylucy-web python manage.py loaddata configuracion_backup.json"
    echo ""
}

# ==============================================================================
# Main
# ==============================================================================
main() {
    echo "================================================================================"
    echo "  PyLucy - Carga de Datos por Defecto"
    echo "================================================================================"
    echo ""

    # Verificar si estamos en el directorio correcto
    if [ ! -d "src" ]; then
        log_warning "No se encuentra el directorio 'src'. Asegúrate de ejecutar desde la raíz del proyecto."
        exit 1
    fi

    # Menú de opciones
    echo "Opciones:"
    echo "  1) Cargar plantillas de email por defecto"
    echo "  2) Mostrar comandos para exportar/importar desde testing"
    echo "  3) Salir"
    echo ""
    read -p "Selecciona una opción [1-3]: " opcion

    case $opcion in
        1)
            log_info "Cargando datos por defecto..."

            # Verificar si estamos dentro de un contenedor o necesitamos usar docker exec
            if [ -f "/.dockerenv" ]; then
                # Estamos dentro del contenedor
                cd src && python cargar_plantillas.py
            else
                # Estamos fuera del contenedor, usar docker exec
                log_info "Ejecutando dentro del contenedor Docker..."
                docker exec -i pylucy-web bash -c "cd /app && python /tmp/cargar_plantillas.py"
            fi

            cargar_plantillas_email
            ;;
        2)
            exportar_datos_testing
            ;;
        3)
            log_info "Saliendo..."
            exit 0
            ;;
        *)
            log_warning "Opción no válida"
            exit 1
            ;;
    esac

    echo ""
    log_success "Proceso completado"
}

# Ejecutar main
main
