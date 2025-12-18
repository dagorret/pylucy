
  📦 Exportar/Importar desde Testing

  # Exportar configuración desde testing
  docker exec pylucy-web python manage.py dumpdata alumnos.Configuracion --indent 2 > config_backup.json

  # Importar en producción
  docker exec -i pylucy-web python manage.py loaddata config_backup.json

