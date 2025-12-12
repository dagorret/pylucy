#!/bin/bash
# Entrypoint para contenedores de PyLucy
# Ejecuta comandos de inicialización antes de iniciar el servidor

set -e

echo "🚀 Iniciando PyLucy..."

# Esperar a que la base de datos esté lista (opcional, ya manejado por healthcheck)
echo "⏳ Esperando base de datos..."
python << END
import sys
import time
import psycopg2
from os import environ

start_time = time.time()
db_ready = False

while time.time() - start_time < 30:
    try:
        conn = psycopg2.connect(
            dbname=environ.get('DB_NAME', 'pylucy'),
            user=environ.get('DB_USER', 'pylucy'),
            password=environ.get('DB_PASSWORD', 'pylucy'),
            host=environ.get('DB_HOST', 'db'),
            port=environ.get('DB_PORT', '5432')
        )
        conn.close()
        db_ready = True
        break
    except psycopg2.OperationalError:
        time.sleep(1)

sys.exit(0 if db_ready else 1)
END

if [ $? -eq 0 ]; then
    echo "✅ Base de datos lista"
else
    echo "❌ No se pudo conectar a la base de datos"
    exit 1
fi

# Ejecutar migraciones
echo "📦 Ejecutando migraciones..."
python manage.py migrate --noinput

# Colectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# Crear superuser por defecto si no existe
echo "👤 Verificando superuser por defecto..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@unrc.edu.ar', 'admin')
    print('✅ Superuser creado: admin / admin')
else:
    print('ℹ️  Superuser admin ya existe')
END

# Inicializar configuración del sistema (solo en testing)
echo "⚙️  Inicializando configuración del sistema..."
python /app/scripts/init_config.py

echo "🎉 Inicialización completada"
echo ""

# Ejecutar el comando pasado como argumentos
exec "$@"
