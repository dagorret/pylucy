● 🚀 Paso a Paso: Servidor Remoto a Producción

  Opción A: Actualizar servidor existente (RECOMENDADO)

  Si ya tienes el servidor corriendo y solo quieres actualizarlo:

  1️⃣ Conectarte al servidor

  ssh usuario@179.43.116.154
  cd /home/usuario/pylucy  # Ajusta la ruta según tu caso

  2️⃣ Actualizar código

  ./update-testing-prod.sh prod

  Listo! El servidor ya está actualizado con el fix.

  ---
  Opción B: Configurar servidor desde cero (COMPLETO)

  Si es la primera vez o quieres hacerlo completo:

  1️⃣ En tu máquina LOCAL: Crear backup

  # Generar backup con toda la configuración
  ./backup-navidad.sh

  Esto crea carpeta: backup-navidad-YYYYMMDD_HHMMSS/

  2️⃣ Copiar backup al servidor

  # Desde tu máquina local
  scp -r backup-navidad-* usuario@179.43.116.154:/home/usuario/pylucy/

  O con rsync (más rápido):
  rsync -avz backup-navidad-* usuario@179.43.116.154:/home/usuario/pylucy/

  3️⃣ En el SERVIDOR: Conectarse

  ssh usuario@179.43.116.154
  cd /home/usuario/pylucy

  4️⃣ Verificar/crear archivo .env para producción

  # Copiar template de configuración
  cp backup-navidad-*/env-example-navidad.txt .env.prod

  # IMPORTANTE: Editar configuración para producción
  nano .env.prod

  Cambios necesarios en .env.prod:
  # Cambiar estas 3 líneas:
  DJANGO_DEBUG=False
  ENVIRONMENT_MODE=production
  ACCOUNT_PREFIX=a

  # El resto puede quedar igual si funciona en testing

  5️⃣ Verificar docker-compose.prod.yml existe

  ls -la docker-compose.prod.yml

  Si no existe, créalo basándote en docker-compose.testing.yml cambiando:
  - El archivo de env: env_file: .env.prod
  - Puerto si es necesario

  6️⃣ Levantar servicios (primera vez)

  # Detener servicios de testing si están corriendo
  docker compose -f docker-compose.testing.yml down

  # Levantar producción
  docker compose -f docker-compose.prod.yml up -d

  # Esperar que PostgreSQL inicie
  sleep 10

  7️⃣ Aplicar migraciones

  docker compose -f docker-compose.prod.yml exec web python manage.py migrate

  8️⃣ Restaurar cursos y configuración (RECOMENDADO)

  cd backup-navidad-*/

  # Restaurar SOLO cursos y configuración (BD limpia)
  docker compose -f ../docker-compose.prod.yml exec -T db \
    psql -U pylucy pylucy < cursos-config.sql

  O restaurar BD completa con alumnos:
  # Restaurar BD COMPLETA (incluye alumnos)
  docker compose -f ../docker-compose.prod.yml exec -T db \
    psql -U pylucy pylucy < database-completa.sql

  9️⃣ Crear superusuario (si es BD nueva)

  cd ..  # Volver a raíz
  docker compose -f docker-compose.prod.yml exec web \
    python manage.py createsuperuser

  🔟 Verificar funcionamiento

  # Ver estado de servicios
  docker compose -f docker-compose.prod.yml ps

  # Ver logs
  docker compose -f docker-compose.prod.yml logs -f web

  # Abrir en navegador
  # http://179.43.116.154:8000/admin

  ---
  ✅ Verificación Final

  1. Admin funciona: http://179.43.116.154:8000/admin
  2. Cursos cargados: Ir a Cursos de Ingreso, ver 10 cursos
  3. Configuración OK: Ir a Configuración
  4. Exportar JSON funciona: Botón "Exportar a JSON" (ya con el fix!)

  ---
  📝 Comandos útiles día a día

  # Actualizar código desde GitHub
  ./update-testing-prod.sh prod

  # Ver logs en tiempo real
  docker compose -f docker-compose.prod.yml logs -f web

  # Reiniciar un servicio
  docker compose -f docker-compose.prod.yml restart web

  # Backup de BD
  docker compose -f docker-compose.prod.yml exec db pg_dump -U pylucy pylucy \
    > backup-prod-$(date +%Y%m%d_%H%M%S).sql


