Comandos para Reiniciar el Servidor Docker

  Opción 1: Reiniciar solo el contenedor web (más rápido)

  docker-compose -f docker-compose.testing.yml restart web

  Opción 2: Reiniciar todos los servicios de PyLucy

  docker-compose -f docker-compose.testing.yml restart

  Opción 3: Reconstruir y reiniciar (si hay cambios en requirements.txt)

  # Detener los contenedores
  docker-compose -f docker-compose.testing.yml down

  # Reconstruir la imagen con las nuevas dependencias
  docker-compose -f docker-compose.testing.yml build web celery celery-beat

  # Levantar todo de nuevo
  docker-compose -f docker-compose.testing.yml up -d

  Opción 4: Ver logs en tiempo real después de reiniciar

  # Reiniciar
  docker-compose -f docker-compose.testing.yml restart web

  # Ver logs
  docker-compose -f docker-compose.testing.yml logs -f web

  Para cambiar al entorno de desarrollo (dev)

  Si prefieres usar el entorno dev en lugar de testing:
  # Detener testing
  docker-compose -f docker-compose.testing.yml down

  # Levantar dev
  docker-compose -f docker-compose.dev.yml up -d

  # Ver logs
  docker-compose -f docker-compose.dev.yml logs -f web

  Verificar que todo esté funcionando

  # Ver estado de los contenedores
  docker-compose -f docker-compose.testing.yml ps

  # Verificar logs del web
  docker-compose -f docker-compose.testing.yml logs web | tail -50

  Recomendación: Como instalaste nuevos paquetes (django-celery-beat, django-select2), usa la Opción 3 para reconstruir las imágenes con las nuevas dependencias.

