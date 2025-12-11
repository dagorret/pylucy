# #ETME - Documentación Testing vs Producción

## 🎯 Objetivo

Este documento detalla TODOS los cambios en el código que se hicieron para modo **TESTING** y cómo cambiarlos a modo **PRODUCCIÓN**.

---

## 🔴 CAMBIOS CRÍTICOS EN EL CÓDIGO

### 1️⃣ **Prefijo en UPN (User Principal Name)**

**Archivo**: `src/alumnos/services.py`
**Líneas**: 136-139

#### Modo TESTING (Actual)
```python
# Línea 137-138
upn = f"test-a{nrodoc}@eco.unrc.edu.ar" if nrodoc else None
```
**Genera**: `test-a12345678@eco.unrc.edu.ar`

#### Modo PRODUCCIÓN
```python
# Cambiar a:
upn = f"a{nrodoc}@eco.unrc.edu.ar" if nrodoc else None
```
**Genera**: `a12345678@eco.unrc.edu.ar`

**⚠️ IMPORTANTE**: Este cambio afecta:
- `email_institucional` del alumno
- `teams_payload.usuario.upn`
- `moodle_payload.usuario.username`
- `moodle_payload.usuario.email`

---

### 2️⃣ **URL de Moodle**

**Archivos a modificar**:
- `src/alumnos/services.py` (líneas 164-183)
- Variables de entorno en `docker-compose.yml`

#### Modo TESTING (Futuro)
```python
moodle_payload = {
    "auth": {
        "domain": "https://sandbox.moodledemo.net",  # ← TESTING
        "token": "MOODLE_SANDBOX_TOKEN",
    },
    # ...
}
```

#### Modo PRODUCCIÓN
```python
moodle_payload = {
    "auth": {
        "domain": "https://moodle.eco.unrc.edu.ar",  # ← PRODUCCIÓN
        "token": "MOODLE_PROD_TOKEN",
    },
    # ...
}
```

---

### 3️⃣ **Servidor de Email**

**Archivo**: `src/pylucy/settings.py`
**Líneas**: 164-171

#### Modo TESTING (Actual)
```python
if os.getenv("DJANGO_ENV") == "development":
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "mailhog"  # ← TESTING (MailHog)
    EMAIL_PORT = 1025
    EMAIL_USE_TLS = False
```

#### Modo PRODUCCIÓN
```python
# Cambiar a servidor SMTP real
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.eco.unrc.edu.ar"  # ← PRODUCCIÓN
EMAIL_PORT = 587
EMAIL_HOST_USER = "noreply@eco.unrc.edu.ar"
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_USE_TLS = True
```

---

### 4️⃣ **Credenciales de Microsoft Teams**

**Archivo**: `src/alumnos/services.py`
**Líneas**: 128-144

#### Modo TESTING
```python
teams_payload = {
    "auth": {
        "tenant": "eco.unrc.edu.ar",
        "client_id": "TEAMS_CLIENT_ID_TESTING",      # ← App Registration de Testing
        "client_secret": "TEAMS_CLIENT_SECRET_TESTING",
    },
    # ...
}
```

#### Modo PRODUCCIÓN
```python
teams_payload = {
    "auth": {
        "tenant": "eco.unrc.edu.ar",
        "client_id": "TEAMS_CLIENT_ID_PROD",          # ← App Registration de Prod
        "client_secret": "TEAMS_CLIENT_SECRET_PROD",
    },
    # ...
}
```

---

## 🔧 SOLUCIÓN: Variables de Entorno

Para evitar cambiar el código cada vez, usar **variables de entorno**.

### Archivo: `src/pylucy/settings.py`

Agregar al final del archivo:

```python
# =============================================================================
# CONFIGURACIÓN TESTING vs PRODUCCIÓN
# =============================================================================

# Modo de ejecución (testing o production)
ENVIRONMENT_MODE = os.getenv("ENVIRONMENT_MODE", "testing").lower()

# Prefijo para cuentas de testing
ACCOUNT_PREFIX = "test-a" if ENVIRONMENT_MODE == "testing" else "a"

# Moodle
MOODLE_BASE_URL = os.getenv(
    "MOODLE_BASE_URL",
    "https://sandbox.moodledemo.net" if ENVIRONMENT_MODE == "testing" else "https://moodle.eco.unrc.edu.ar"
)
MOODLE_WSTOKEN = os.getenv("MOODLE_WSTOKEN", "")

# Microsoft Teams / Graph API
TEAMS_TENANT = os.getenv("TEAMS_TENANT", "eco.unrc.edu.ar")
TEAMS_CLIENT_ID = os.getenv("TEAMS_CLIENT_ID", "")
TEAMS_CLIENT_SECRET = os.getenv("TEAMS_CLIENT_SECRET", "")
```

### Archivo: `src/alumnos/services.py`

Modificar línea 136-139:

```python
from django.conf import settings

# ...

nrodoc = str(lista_item.get("nrodoc") or "").strip()
# Usar prefijo según modo (test-a en testing, a en producción)
upn = f"{settings.ACCOUNT_PREFIX}{nrodoc}@eco.unrc.edu.ar" if nrodoc else None
email_inst = upn or (personal.get("email_institucional") or "").strip() or None
```

Modificar línea 128-144 (teams_payload):

```python
teams_payload = {
    "auth": {
        "tenant": settings.TEAMS_TENANT,
        "client_id": settings.TEAMS_CLIENT_ID,
        "client_secret": settings.TEAMS_CLIENT_SECRET,
    },
    # ...
}
```

Modificar línea 164-183 (moodle_payload):

```python
moodle_payload = {
    "auth": {
        "domain": settings.MOODLE_BASE_URL,
        "token": settings.MOODLE_WSTOKEN,
    },
    # ...
}
```

---

## 📋 Archivos de Configuración Docker

### Archivo: `docker-compose.dev.yml` (TESTING)

```yaml
services:
  web:
    environment:
      - ENVIRONMENT_MODE=testing           # ← TESTING MODE
      - DJANGO_ENV=development

      # Email (MailHog)
      - EMAIL_HOST=mailhog
      - EMAIL_PORT=1025

      # Moodle Sandbox
      - MOODLE_BASE_URL=https://sandbox.moodledemo.net
      - MOODLE_WSTOKEN=OBTENER_DEL_SANDBOX

      # Teams (App Registration de Testing)
      - TEAMS_TENANT=eco.unrc.edu.ar
      - TEAMS_CLIENT_ID=CLIENT_ID_TESTING
      - TEAMS_CLIENT_SECRET=CLIENT_SECRET_TESTING
```

### Archivo: `docker-compose.prod.yml` (PRODUCCIÓN)

```yaml
services:
  web:
    environment:
      - ENVIRONMENT_MODE=production        # ← PRODUCTION MODE
      - DJANGO_ENV=production

      # Email (SMTP Real)
      - EMAIL_HOST=smtp.eco.unrc.edu.ar
      - EMAIL_PORT=587
      - EMAIL_HOST_USER=noreply@eco.unrc.edu.ar
      - EMAIL_HOST_PASSWORD=${EMAIL_PASSWORD}  # Desde .env secreto

      # Moodle Producción
      - MOODLE_BASE_URL=https://moodle.eco.unrc.edu.ar
      - MOODLE_WSTOKEN=${MOODLE_PROD_TOKEN}     # Desde .env secreto

      # Teams (App Registration de Producción)
      - TEAMS_TENANT=eco.unrc.edu.ar
      - TEAMS_CLIENT_ID=${TEAMS_PROD_CLIENT_ID}
      - TEAMS_CLIENT_SECRET=${TEAMS_PROD_CLIENT_SECRET}
```

---

## 🔄 Proceso de Cambio Testing → Producción

### Paso 1: Actualizar settings.py
✅ Agregar variables de configuración (sección anterior)

### Paso 2: Actualizar services.py
✅ Cambiar valores hardcoded por `settings.VARIABLE`

### Paso 3: Crear archivo .env.prod
```bash
# .env.prod (NO commitear al repo)
ENVIRONMENT_MODE=production
EMAIL_PASSWORD=contraseña_smtp_real
MOODLE_PROD_TOKEN=token_moodle_produccion
TEAMS_PROD_CLIENT_ID=app_registration_prod_id
TEAMS_PROD_CLIENT_SECRET=app_registration_prod_secret
```

### Paso 4: Cambiar docker-compose
```bash
# Testing
docker compose -f docker-compose.dev.yml up

# Producción
docker compose -f docker-compose.prod.yml --env-file .env.prod up
```

### Paso 5: Verificar modo actual
Agregar comando Django para verificar:

```python
# src/alumnos/management/commands/check_environment.py
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Verifica el modo de ejecución actual'

    def handle(self, *args, **options):
        mode = settings.ENVIRONMENT_MODE
        prefix = settings.ACCOUNT_PREFIX
        moodle = settings.MOODLE_BASE_URL

        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(f"MODO ACTUAL: {mode.upper()}")
        self.stdout.write(f"{'='*50}")
        self.stdout.write(f"Prefijo cuentas: {prefix}")
        self.stdout.write(f"Moodle URL: {moodle}")
        self.stdout.write(f"Email Host: {settings.EMAIL_HOST}")
        self.stdout.write(f"{'='*50}\n")

        if mode == "testing":
            self.stdout.write(self.style.WARNING("⚠️  MODO TESTING ACTIVO"))
        else:
            self.stdout.write(self.style.SUCCESS("✓ MODO PRODUCCIÓN ACTIVO"))
```

Ejecutar:
```bash
docker exec pylucy-web-dev python manage.py check_environment
```

---

## ⚠️ CHECKLIST DE SEGURIDAD

Antes de pasar a producción:

- [ ] `ENVIRONMENT_MODE=production` en docker-compose.prod.yml
- [ ] Credenciales reales en `.env.prod` (NO en el código)
- [ ] `.env.prod` está en `.gitignore`
- [ ] Prefijo `test-` removido (se usa solo `a`)
- [ ] URL Moodle apunta a moodle.eco.unrc.edu.ar
- [ ] SMTP apunta a smtp.eco.unrc.edu.ar
- [ ] App Registration de Teams es la de PRODUCCIÓN
- [ ] MailHog deshabilitado en producción
- [ ] Ejecutar `check_environment` para verificar

---

## 🧪 Testing de Configuración

### Modo Testing
```bash
# Variable de entorno
export ENVIRONMENT_MODE=testing

# Verificar
python manage.py check_environment

# Consumir datos
# → Debe crear: test-a12345678@eco.unrc.edu.ar
```

### Modo Producción
```bash
# Variable de entorno
export ENVIRONMENT_MODE=production

# Verificar
python manage.py check_environment

# Consumir datos
# → Debe crear: a12345678@eco.unrc.edu.ar
```

---

## 📊 Tabla Resumen de Diferencias

| Componente | Testing | Producción |
|------------|---------|------------|
| **UPN** | `test-a12345678@eco.unrc.edu.ar` | `a12345678@eco.unrc.edu.ar` |
| **Email Server** | MailHog (localhost:1025) | smtp.eco.unrc.edu.ar:587 |
| **Moodle URL** | sandbox.moodledemo.net | moodle.eco.unrc.edu.ar |
| **Teams App** | App Registration Testing | App Registration Prod |
| **Reset data** | Moodle cada hora, Teams manual | Datos persistentes |
| **Variable ENV** | `ENVIRONMENT_MODE=testing` | `ENVIRONMENT_MODE=production` |

---

## 🔐 Secretos (NO commitear)

Archivo: `.env.prod` (debe estar en `.gitignore`)

```bash
# Email
EMAIL_PASSWORD=contraseña_smtp_real_aqui

# Moodle
MOODLE_PROD_TOKEN=token_obtenido_de_moodle_admin

# Microsoft Teams
TEAMS_PROD_CLIENT_ID=12345678-1234-1234-1234-123456789abc
TEAMS_PROD_CLIENT_SECRET=secreto_muy_largo_de_azure_ad
```

---

## 📝 Notas Importantes

1. **NUNCA hardcodear** credenciales de producción en el código
2. **SIEMPRE** usar variables de entorno para secretos
3. **Prefijo test-** debe usarse SOLO en testing
4. **Verificar modo** con `check_environment` antes de ejecutar en prod
5. **Backup** antes de ejecutar en producción por primera vez

---

**Tag**: #ETME (Environment Testing Mode)
**Última actualización**: 2025-12-08
**Autor**: Sistema Lucy AMS
