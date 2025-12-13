  ✅ Scripts Creados

  1. 🚀 update-testing-prod.sh - Actualización Automática

  Actualiza el código y reinicia servicios automáticamente:

  # Para testing
  ./update-testing-prod.sh testing

  # Para producción
  ./update-testing-prod.sh prod

  Qué hace:
  1. ✅ git pull origin main
  2. ✅ Detecta y aplica migraciones automáticamente
  3. ✅ collectstatic (solo en prod)
  4. ✅ Reinicia web, celery, celery-beat
  5. ✅ Muestra estado y logs recientes
  6. ✅ Muestra comandos útiles al final

  ---
  2. 🛠️ comandos-comunes.sh - Comandos Útiles Rápidos

  Acceso rápido a comandos frecuentes:

  # Ver logs en tiempo real
  ./comandos-comunes.sh logs testing

  # Abrir Django shell
  ./comandos-comunes.sh shell prod

  # Ver estado de servicios
  ./comandos-comunes.sh status testing

  # Hacer backup de BD
  ./comandos-comunes.sh backup-db prod

  # Importar configuración
  ./comandos-comunes.sh import-config testing

  # Verificar configuración
  ./comandos-comunes.sh verify-config testing

  # Reiniciar solo web
  ./comandos-comunes.sh restart-web testing

  # Ver logs de Celery
  ./comandos-comunes.sh logs-celery testing

  Comandos disponibles:
  - status - Estado de servicios
  - logs / logs-all / logs-celery / logs-beat - Ver logs
  - shell / dbshell - Abrir shells
  - migrate / makemigrations - Migraciones
  - restart / restart-web / restart-celery - Reiniciar
  - backup-db - Backup PostgreSQL
  - import-config / export-config - Gestión config JSON
  - verify-config - Verificar config actual

  ---
  📝 Ahora en tu servidor solo haces:

  # Actualizar y reiniciar todo
  ./update-testing-prod.sh testing

  # O si quieres ver logs después
  ./comandos-comunes.sh logs testing

