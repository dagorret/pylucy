# Backend de Email con Microsoft Graph API

Este documento describe cómo configurar y utilizar el backend personalizado de email que usa Microsoft Graph API en lugar de SMTP tradicional.

## Ubicación del Backend

- **Módulo**: `alumnos.backends.msgraph`
- **Clase**: `MicrosoftGraphEmailBackend`
- **Archivos**:
  - `src/alumnos/backends/__init__.py`
  - `src/alumnos/backends/msgraph.py`

## ¿Por qué usar Microsoft Graph API en lugar de SMTP?

### Ventajas

1. **No requiere habilitar SMTP** en Exchange/Office 365 (que a menudo está deshabilitado por seguridad)
2. **Mejor control de errores** y seguimiento detallado
3. **Integración nativa** con Azure AD y Microsoft 365
4. **Características avanzadas**: tracking de lectura, prioridad, categorías, etc.
5. **Mismo token OAuth2** que ya se usa para Teams (reutiliza credenciales)

### Desventajas

1. Requiere configuración de permisos en Azure AD
2. Necesita conectividad con Graph API (no funciona offline)
3. Más complejo de configurar inicialmente

## Configuración

### 1. Permisos en Azure AD

La aplicación de Azure AD debe tener el siguiente permiso de **Application permissions** (no delegated):

- **Mail.Send**: Permite enviar emails como cualquier usuario

#### Pasos para configurar permisos:

1. Ir a [Azure Portal](https://portal.azure.com)
2. Navegar a **Azure Active Directory** > **App registrations**
3. Seleccionar tu aplicación (la misma que usas para Teams)
4. Ir a **API permissions**
5. Click en **Add a permission** > **Microsoft Graph** > **Application permissions**
6. Buscar y seleccionar **Mail.Send**
7. Click en **Add permissions**
8. **IMPORTANTE**: Click en **Grant admin consent** (requiere admin del tenant)

### 2. Configuración en Django

#### Opción A: Variables de Entorno (recomendado)

Edita tu archivo `.env`:

```bash
# Backend de Email
EMAIL_BACKEND=alumnos.backends.msgraph.MicrosoftGraphEmailBackend

# Credenciales de Azure AD (las mismas que para Teams)
TEAMS_TENANT=tu-tenant-id
TEAMS_CLIENT_ID=tu-client-id
TEAMS_CLIENT_SECRET=tu-client-secret

# Email que se usará como remitente
DEFAULT_FROM_EMAIL=noreply@eco.unrc.edu.ar
```

#### Opción B: Base de Datos

Si prefieres configurar desde el panel de administración:

1. Ir al admin de Django: `/admin/`
2. Navegar a **Configuración** (singleton)
3. Configurar:
   - **Teams Tenant ID**: tu-tenant-id
   - **Teams Client ID**: tu-client-id
   - **Teams Client Secret**: tu-client-secret
   - **Email From**: noreply@eco.unrc.edu.ar

Luego en `settings.py`:

```python
EMAIL_BACKEND = "alumnos.backends.msgraph.MicrosoftGraphEmailBackend"
```

### 3. Usuario Remitente

El email configurado en `DEFAULT_FROM_EMAIL` debe ser:

1. Un usuario **real** en tu tenant de Microsoft 365
2. Tener un buzón activo (mailbox)
3. NO puede ser un alias o grupo de distribución

**Recomendación**: Crear un usuario de servicio dedicado, ej: `noreply@eco.unrc.edu.ar`

## Uso

Una vez configurado, el uso es **exactamente igual** al SMTP tradicional. Todas las funciones de Django funcionan sin cambios:

### Envío simple

```python
from django.core.mail import send_mail

send_mail(
    subject='Asunto del email',
    message='Contenido en texto plano',
    from_email='noreply@eco.unrc.edu.ar',
    recipient_list=['alumno@ejemplo.com'],
)
```

### Envío con HTML

```python
from django.core.mail import EmailMessage

msg = EmailMessage(
    subject='Bienvenido a Lucy AMS',
    body='Versión en texto plano',
    from_email='noreply@eco.unrc.edu.ar',
    to=['alumno@ejemplo.com'],
)
msg.attach_alternative('<h1>Bienvenido</h1><p>HTML aquí</p>', "text/html")
msg.send()
```

### Uso en servicios existentes

El `EmailService` de Lucy ya usa internamente `send_mail()`, por lo que **no requiere cambios**:

```python
from alumnos.services.email_service import EmailService

service = EmailService()
service.send_credentials_email(alumno, teams_data)
```

## Monitoreo y Logs

### Logs en Base de Datos

El backend registra automáticamente eventos en el modelo `Log`:

- **SUCCESS**: Email enviado correctamente
- **ERROR**: Fallos en autenticación, conexión o envío

Ver logs en: `/admin/alumnos/log/`

### Logs en Consola

Todos los eventos también se registran vía `logging`:

```bash
# Ver logs en desarrollo
docker compose logs -f web

# Filtrar solo logs de email
docker compose logs -f web | grep "MicrosoftGraphEmailBackend"
```

### Códigos de Error

- **MSGraph-001**: Credenciales inválidas (tenant_id, client_id o client_secret incorrectos)
- **MSGraph-002**: Error de conexión a Microsoft Graph API
- **HTTP 401**: Token expirado o inválido
- **HTTP 403**: Permisos insuficientes (falta Mail.Send)
- **HTTP 404**: Usuario remitente no existe en el tenant

## Cambiar entre SMTP y Graph API

### Volver a SMTP

Edita `.env`:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@eco.unrc.edu.ar
EMAIL_HOST_PASSWORD=contraseña-del-usuario
```

### Usar Graph API

Edita `.env`:

```bash
EMAIL_BACKEND=alumnos.backends.msgraph.MicrosoftGraphEmailBackend
```

**No requiere reiniciar el servidor** en desarrollo (Django recarga automáticamente).

En producción, reinicia los contenedores:

```bash
docker compose -f docker-compose.prod.yml restart web
```

## Troubleshooting

### Error: "Credenciales inválidas"

**Causa**: TEAMS_TENANT, TEAMS_CLIENT_ID o TEAMS_CLIENT_SECRET incorrectos

**Solución**:
1. Verificar que los valores en `.env` coincidan con Azure Portal
2. Verificar que no haya espacios extra en las variables
3. Verificar que el tenant ID sea el correcto (puede ser el tenant ID o el nombre del dominio)

### Error: "HTTP 403 Forbidden"

**Causa**: Falta el permiso `Mail.Send` o no se dio consentimiento de administrador

**Solución**:
1. Ir a Azure Portal > App registrations > Tu app > API permissions
2. Verificar que `Mail.Send` esté en la lista
3. Click en **Grant admin consent for [tu organización]**
4. Esperar 5 minutos y volver a intentar

### Error: "HTTP 404 Not Found"

**Causa**: El usuario en `DEFAULT_FROM_EMAIL` no existe o no tiene buzón

**Solución**:
1. Verificar que el email exista en Microsoft 365
2. Verificar que tenga licencia asignada
3. Verificar que el buzón esté activo (puede tardar hasta 24h después de crear el usuario)

### Emails no se envían pero no hay errores

**Causa**: `fail_silently=True` está suprimiendo errores

**Solución**:
1. Revisar logs en BD: `/admin/alumnos/log/`
2. Revisar logs en consola: `docker compose logs web`
3. Cambiar temporalmente a `fail_silently=False` para debugging

## Características Avanzadas

### Múltiples destinatarios

```python
send_mail(
    subject='Asunto',
    message='Contenido',
    from_email='noreply@eco.unrc.edu.ar',
    recipient_list=['alumno1@ejemplo.com', 'alumno2@ejemplo.com'],
)
```

### CC y BCC

```python
from django.core.mail import EmailMessage

msg = EmailMessage(
    subject='Asunto',
    body='Contenido',
    from_email='noreply@eco.unrc.edu.ar',
    to=['destinatario@ejemplo.com'],
    cc=['copia@ejemplo.com'],
    bcc=['copia-oculta@ejemplo.com'],
)
msg.send()
```

### Reply-To

```python
msg = EmailMessage(
    subject='Asunto',
    body='Contenido',
    from_email='noreply@eco.unrc.edu.ar',
    to=['destinatario@ejemplo.com'],
    reply_to=['soporte@eco.unrc.edu.ar'],
)
msg.send()
```

## Comparación: SMTP vs Graph API

| Característica | SMTP | Graph API |
|----------------|------|-----------|
| Configuración inicial | Simple | Requiere Azure AD |
| Requiere contraseña de usuario | Sí | No (usa OAuth2) |
| Requiere habilitar SMTP en M365 | Sí | No |
| Autenticación | Usuario/Password o App Password | OAuth2 Client Credentials |
| Errores detallados | Limitados | Muy detallados (JSON) |
| Rate limiting | Por conexión SMTP | Por API calls |
| Reutiliza credenciales Teams | No | Sí |
| Funciona offline | Sí (con relay local) | No |

## Arquitectura Interna

### Flujo de Envío

1. Django llama `send_mail()` o `EmailMessage.send()`
2. El backend obtiene token OAuth2 (cacheado en memoria)
3. Convierte `EmailMessage` de Django al formato JSON de Graph API
4. Hace `POST /v1.0/users/{from_email}/sendMail`
5. Registra el resultado en logs (BD + consola)
6. Retorna número de emails enviados

### Reutilización de Código

El backend reutiliza el mismo patrón de `TeamsService`:

- Autenticación OAuth2 con Client Credentials Flow
- Fallback de configuración: BD → ENV
- Logging consistente con `log_to_db()`
- Manejo de errores similar

## Testing

### Modo Console (desarrollo)

Para ver los emails sin enviarlos realmente:

```bash
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Los emails se imprimirán en la consola en lugar de enviarse.

### Modo MailHog (desarrollo)

Para testing visual sin Graph API:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mailhog
EMAIL_PORT=1025
```

Los emails se capturan en MailHog: http://localhost:8025

## Referencias

- [Microsoft Graph API - Send Mail](https://learn.microsoft.com/en-us/graph/api/user-sendmail)
- [Django Email Backends](https://docs.djangoproject.com/en/5.0/topics/email/#email-backends)
- [Azure AD Client Credentials Flow](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow)
