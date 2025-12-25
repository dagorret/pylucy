#!/bin/bash

# ============================================
# Script de Backup Completo - PyLucy Navidad
# ============================================
# Exporta cursos, configuración y base de datos
# Genera carpeta con todo lo necesario para producción

set -e  # Salir si hay error

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FECHA=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup-navidad-$FECHA"

echo ""
echo "============================================"
echo "  PyLucy - Backup Completo Navidad 2025"
echo "============================================"
echo ""

# Crear directorio de backup
echo -e "${BLUE}[1/6]${NC} Creando directorio de backup..."
mkdir -p $BACKUP_DIR
echo -e "${GREEN}✓${NC} Directorio creado: $BACKUP_DIR"

# 1. Backup SQL de cursos y configuración (solo datos)
echo ""
echo -e "${BLUE}[2/6]${NC} Exportando cursos y configuración (SQL)..."
docker compose -f docker-compose.testing.yml exec -T db pg_dump -U pylucy pylucy \
  --table=cursos_cursoingreso \
  --table=alumnos_configuracion \
  --data-only \
  --column-inserts \
  > $BACKUP_DIR/cursos-config.sql
echo -e "${GREEN}✓${NC} Cursos y configuración exportados"

# 2. Backup completo de la BD
echo ""
echo -e "${BLUE}[3/6]${NC} Exportando base de datos completa..."
docker compose -f docker-compose.testing.yml exec -T db pg_dump -U pylucy pylucy \
  > $BACKUP_DIR/database-completa.sql
echo -e "${GREEN}✓${NC} Base de datos completa exportada"

# 3. Copiar archivos de configuración
echo ""
echo -e "${BLUE}[4/6]${NC} Copiando archivos de configuración..."
cp env-example-navidad.txt $BACKUP_DIR/ 2>/dev/null || echo "  (env-example-navidad.txt no encontrado)"
cp env-testing.txt $BACKUP_DIR/ 2>/dev/null || echo "  (env-testing.txt no encontrado)"
cp env-production.txt $BACKUP_DIR/ 2>/dev/null || echo "  (env-production.txt no encontrado)"
cp README-ENV.md $BACKUP_DIR/ 2>/dev/null || echo "  (README-ENV.md no encontrado)"
cp todo-email.txt $BACKUP_DIR/ 2>/dev/null || echo "  (todo-email.txt no encontrado)"
echo -e "${GREEN}✓${NC} Archivos de configuración copiados"

# 4. Exportar información de Docker
echo ""
echo -e "${BLUE}[5/6]${NC} Exportando información de Docker..."
docker compose -f docker-compose.testing.yml ps > $BACKUP_DIR/docker-services.txt
echo -e "${GREEN}✓${NC} Estado de servicios exportado"

# 5. Crear archivo de instrucciones
echo ""
echo -e "${BLUE}[6/6]${NC} Generando instrucciones de restauración..."
cat > $BACKUP_DIR/INSTRUCCIONES-RESTAURACION.txt << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║     INSTRUCCIONES DE RESTAURACIÓN - PyLucy Navidad 2025       ║
╚════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════
PASO 1: Copiar backup al servidor de producción
═══════════════════════════════════════════════════════════════

En tu máquina local:

  scp -r backup-navidad-* usuario@servidor:/home/usuario/pylucy/

O usando rsync (más rápido):

  rsync -avz backup-navidad-* usuario@servidor:/home/usuario/pylucy/


═══════════════════════════════════════════════════════════════
PASO 2: En el servidor, preparar el entorno
═══════════════════════════════════════════════════════════════

cd /home/usuario/pylucy/backup-navidad-*/

# Copiar archivo de configuración
cp env-example-navidad.txt ../.env.prod

# IMPORTANTE: Editar .env.prod si es necesario
# - Cambiar ENVIRONMENT_MODE=production
# - Cambiar ACCOUNT_PREFIX=a
# - Cambiar DJANGO_DEBUG=False
nano ../.env.prod


═══════════════════════════════════════════════════════════════
PASO 3: Levantar servicios (primera vez)
═══════════════════════════════════════════════════════════════

cd ..  # Volver a la raíz de pylucy

# Levantar servicios
docker compose -f docker-compose.prod.yml up -d

# Esperar que la BD esté lista
sleep 10


═══════════════════════════════════════════════════════════════
PASO 4A: Restaurar SOLO cursos y configuración (RECOMENDADO)
═══════════════════════════════════════════════════════════════

# Usar este método si quieres empezar con BD limpia
# Solo restaura cursos y configuración del sistema

cd backup-navidad-*/

docker compose -f ../docker-compose.prod.yml exec -T db \
  psql -U pylucy pylucy < cursos-config.sql

# Aplicar migraciones
docker compose -f ../docker-compose.prod.yml exec web \
  python manage.py migrate


═══════════════════════════════════════════════════════════════
PASO 4B: Restaurar base de datos COMPLETA (alternativa)
═══════════════════════════════════════════════════════════════

# Usar este método si quieres copiar TODO incluyendo alumnos

cd backup-navidad-*/

docker compose -f ../docker-compose.prod.yml exec -T db \
  psql -U pylucy pylucy < database-completa.sql


═══════════════════════════════════════════════════════════════
PASO 5: Reiniciar servicios
═══════════════════════════════════════════════════════════════

cd ..  # Volver a la raíz

docker compose -f docker-compose.prod.yml restart web celery celery-beat


═══════════════════════════════════════════════════════════════
PASO 6: Verificar funcionamiento
═══════════════════════════════════════════════════════════════

# Ver logs en tiempo real
docker compose -f docker-compose.prod.yml logs -f web

# Verificar servicios
docker compose -f docker-compose.prod.yml ps

# Acceder al admin de Django
# http://tu-servidor:8000/admin


═══════════════════════════════════════════════════════════════
COMANDOS ÚTILES EN PRODUCCIÓN
═══════════════════════════════════════════════════════════════

# Actualizar código desde Git
./update-testing-prod.sh prod

# Ver logs
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f celery

# Reiniciar un servicio
docker compose -f docker-compose.prod.yml restart web

# Shell de Django
docker compose -f docker-compose.prod.yml exec web python manage.py shell

# Crear superusuario
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Backup de la BD en producción
docker compose -f docker-compose.prod.yml exec db pg_dump -U pylucy pylucy \
  > backup-prod-$(date +%Y%m%d_%H%M%S).sql


═══════════════════════════════════════════════════════════════
ARCHIVOS EN ESTE BACKUP
═══════════════════════════════════════════════════════════════

cursos-config.sql              - Solo cursos y configuración (RÁPIDO)
database-completa.sql          - Base de datos completa con alumnos
env-example-navidad.txt        - Configuración de entorno actual
env-testing.txt                - Template para testing
env-production.txt             - Template para producción
README-ENV.md                  - Documentación de variables
todo-email.txt                 - Notas para implementar emails
docker-services.txt            - Estado de servicios Docker
INSTRUCCIONES-RESTAURACION.txt - Este archivo


═══════════════════════════════════════════════════════════════
SOLUCIÓN DE PROBLEMAS
═══════════════════════════════════════════════════════════════

Error: "relation does not exist"
  → Las tablas no existen, primero ejecuta las migraciones:
    docker compose -f docker-compose.prod.yml exec web python manage.py migrate

Error: "role pylucy does not exist"
  → El usuario de BD no existe, verifica docker-compose.prod.yml

Error: "permission denied"
  → Verifica permisos del archivo .env.prod

Servicios no inician:
  → Verifica logs: docker compose -f docker-compose.prod.yml logs


═══════════════════════════════════════════════════════════════
SOPORTE
═══════════════════════════════════════════════════════════════

Documentación completa: README-ENV.md
Backup creado: $(date)
EOF

# Crear resumen del backup
cat > $BACKUP_DIR/RESUMEN-BACKUP.txt << EOF
RESUMEN DEL BACKUP
==================
Fecha: $(date)
Directorio: $BACKUP_DIR

Archivos SQL:
$(ls -lh $BACKUP_DIR/*.sql)

Archivos de configuración:
$(ls -lh $BACKUP_DIR/*.txt $BACKUP_DIR/*.md 2>/dev/null || echo "  No hay archivos adicionales")

Tamaño total:
$(du -sh $BACKUP_DIR)

SIGUIENTE PASO:
===============
1. Lee INSTRUCCIONES-RESTAURACION.txt
2. Copia esta carpeta al servidor de producción
3. Sigue los pasos del archivo de instrucciones

COMANDO RÁPIDO:
===============
scp -r $BACKUP_DIR usuario@servidor:/home/usuario/pylucy/
EOF

# Mostrar resumen
echo ""
echo "============================================"
echo -e "${GREEN}✅ BACKUP COMPLETADO EXITOSAMENTE${NC}"
echo "============================================"
echo ""
echo "📦 Backup creado en: ${YELLOW}$BACKUP_DIR${NC}"
echo ""
echo "📄 Archivos generados:"
echo "   • cursos-config.sql (solo cursos y configuración)"
echo "   • database-completa.sql (BD completa)"
echo "   • env-example-navidad.txt (configuración actual)"
echo "   • INSTRUCCIONES-RESTAURACION.txt"
echo "   • RESUMEN-BACKUP.txt"
echo ""
echo "📊 Tamaño del backup:"
du -sh $BACKUP_DIR
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SIGUIENTE PASO:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Lee las instrucciones:"
echo "   cat $BACKUP_DIR/INSTRUCCIONES-RESTAURACION.txt"
echo ""
echo "2. Copia el backup al servidor de producción:"
echo "   scp -r $BACKUP_DIR usuario@servidor:/home/usuario/pylucy/"
echo ""
echo "3. En el servidor, sigue las instrucciones"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
