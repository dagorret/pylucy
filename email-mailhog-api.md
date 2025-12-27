  # EMAIL - SMTP con MailHog (testing)
  #EMAIL_BACKEND=alumnos.backends.graph_email_backend.GraphEmailBackend  # Desactivado
  EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
  EMAIL_HOST=mailhog
  EMAIL_PORT=1025
  EMAIL_USE_TLS=false
  EMAIL_HOST_USER=
  EMAIL_HOST_PASSWORD=

  DEFAULT_FROM_EMAIL=lucy@eco.unrc.edu.ar

  Solo corregí los comentarios para que no digan "No usado con Graph API" cuando estás usando MailHog. Pero funcionalmente está correcto.

