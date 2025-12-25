  #!/bin/bash
  # backup-navidad.sh - Exporta TODO lo necesario

  FECHA=$(date +%Y%m%d_%H%M%S)
  BACKUP_DIR="backup-navidad-$FECHA"

  echo "Creando backup completo en $BACKUP_DIR..."
  mkdir -p $BACKUP_DIR

  # 1. Backup SQL de cursos y configuración
  echo "📦 Exportando cursos y configuración (SQL)..."
  docker compose -f docker-compose.testing.yml exec db pg_dump -U pylucy pylucy \
    --table=cursos_cursoingreso \
    --table=alumnos_configuracion \
    --data-only \
    --column-inserts \
    > $BACKUP_DIR/cursos-config.sql

  # 2. Backup completo de la BD
  echo "📦 Exportando base de datos completa..."
  docker compose -f docker-compose.testing.yml exec db pg_dump -U pylucy pylucy \
    > $BACKUP_DIR/database-completa.sql

  # 3. Copiar archivo de configuración
  echo "📦 Copiando archivos de configuración..."
  cp env-example-navidad.txt $BACKUP_DIR/
  cp env-testing.txt $BACKUP_DIR/
  cp env-production.txt $BACKUP_DIR/
  cp README-ENV.md $BACKUP_DIR/

