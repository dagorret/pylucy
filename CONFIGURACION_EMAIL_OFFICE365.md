# 📧 Configuración de Email con Office 365

Guía completa para configurar PyLucy para enviar emails a través de Office 365.

---

## 📋 Requisitos Previos

1. **Cuenta de Office 365** con permiso para enviar correos
2. **SMTP habilitado** en la cuenta de Office 365
3. **Autenticación moderna deshabilitada** o usar App Password

---

## ⚙️ Configuración en el archivo `.env`

Agrega estas variables al archivo `.env` (desarrollo) o `.env.prod` (producción):

```bash
# ============================================
# CONFIGURACIÓN DE EMAIL - OFFICE 365
# ============================================

# SMTP de Office 365
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False

# Credenciales de la cuenta de Office 365
EMAIL_HOST_USER=tu-usuario@eco.unrc.edu.ar
EMAIL_HOST_PASSWORD=tu-password-aqui

# Dirección "From" para los emails
EMAIL_FROM=no-reply@eco.unrc.edu.ar
```

### 📝 Notas sobre las credenciales

- **EMAIL_HOST_USER**: Email completo de Office 365 (ej: `admin@eco.unrc.edu.ar`)
- **EMAIL_HOST_PASSWORD**:
  - Si usas autenticación moderna: Usa una **App Password**
  - Si está deshabilitada: Usa tu password normal

---

## 🔐 Crear App Password en Office 365

Si tienes autenticación multifactor (MFA) habilitada:

1. Ir a [https://account.microsoft.com/security](https://account.microsoft.com/security)
2. **Security** → **Advanced security options**
3. **App passwords** → **Create a new app password**
4. Copiar el password generado
5. Usarlo en `EMAIL_HOST_PASSWORD`

---

## 🧪 Probar Configuración

### Desde el Admin de Django

1. Ir al **Dashboard** del admin de Django
2. Buscar la sección **"📧 Probar Envío de Email"**
3. Ingresar un email de destino
4. Click en **"📤 Enviar Email de Prueba"**
5. Verificar que llegue el email

![Prueba de Email](docs/test-email-form.png)

### Desde la línea de comandos

```bash
# Dentro del contenedor Docker
docker compose exec web python manage.py shell

# Ejecutar:
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    subject='Prueba de Email',
    message='Este es un email de prueba',
    from_email=settings.EMAIL_FROM,
    recipient_list=['tu-email@ejemplo.com'],
    fail_silently=False
)
```

---

## 🚀 Alternativas a Office 365

### MailHog (Desarrollo)

Para desarrollo local, usa MailHog (ya configurado en `docker-compose.dev.yml`):

```bash
EMAIL_HOST=mailhog
EMAIL_PORT=1025
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=False
EMAIL_USE_SSL=False
EMAIL_FROM=dev@localhost
```

**Acceso**: http://localhost:8025

### Gmail SMTP

Si prefieres usar Gmail:

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
EMAIL_FROM=tu-email@gmail.com
```

**Nota**: Debes generar una App Password en Google Account Security.

---

## 🐛 Troubleshooting

### Error: "SMTPAuthenticationError"

**Causa**: Credenciales incorrectas o autenticación moderna bloqueada

**Solución**:
1. Verificar que `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD` sean correctos
2. Usar App Password si tienes MFA habilitado
3. Verificar que SMTP esté habilitado en la cuenta de Office 365

### Error: "SMTPServerDisconnected"

**Causa**: Puerto o configuración TLS/SSL incorrecta

**Solución**:
```bash
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
```

### Error: "Name or service not known"

**Causa**: No se puede resolver el hostname de SMTP

**Solución**:
- Verificar conectividad de red
- Asegurarse de que el contenedor Docker puede acceder a internet

### Los emails no llegan (sin errores)

**Posibles causas**:
1. **Emails en spam**: Verificar carpeta de spam
2. **Límite de envíos**: Office 365 tiene límites (500-1000 emails/día)
3. **Remitente bloqueado**: Verificar que `EMAIL_FROM` sea una dirección válida del dominio

---

## 📊 Monitoreo de Emails

### Ver logs de envío

```bash
# Ver logs del contenedor web
docker compose logs -f web | grep "Email"

# Ver logs de Celery (para emails asíncronos)
docker compose logs -f celery | grep "Email"
```

### Ver en base de datos

Los intentos de envío se registran en el modelo `Log`:

```python
# Django shell
from alumnos.models import Log

# Ver últimos emails enviados
Log.objects.filter(modulo='email_service').order_by('-fecha')[:10]
```

---

## 🔄 Estrategia de Envío Recomendada

### Para Producción (Office 365)

```bash
# .env.prod
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=admin@eco.unrc.edu.ar
EMAIL_HOST_PASSWORD=app-password-here
EMAIL_FROM=no-reply@eco.unrc.edu.ar
```

### Para Testing/Desarrollo (MailHog)

```bash
# .env.dev
EMAIL_HOST=mailhog
EMAIL_PORT=1025
EMAIL_USE_TLS=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_FROM=test@localhost
```

---

## 📚 Referencias

- [Office 365 SMTP Settings](https://support.microsoft.com/en-us/office/pop-imap-and-smtp-settings-for-outlook-com-d088b986-291d-42b8-9564-9c414e2aa040)
- [Django Email Settings](https://docs.djangoproject.com/en/5.0/topics/email/)
- [MailHog Documentation](https://github.com/mailhog/MailHog)

---

## ✅ Checklist de Configuración

- [ ] Configurar variables `EMAIL_*` en archivo `.env`
- [ ] Reiniciar servicios Docker
- [ ] Probar envío desde dashboard admin
- [ ] Verificar que llegue el email de prueba
- [ ] Configurar monitoreo de logs
- [ ] Documentar credenciales en lugar seguro (1Password, etc.)

---

**Última actualización**: 26 de diciembre de 2025
