# Sistema de Fallback: Configuración DB → ENV

## Resumen

El sistema implementa un **fallback automático** de configuración:
1. **Primero** intenta leer de la base de datos (tabla `Configuracion`)
2. **Si está vacío**, lee de las variables de entorno (`.env`)

Esto permite:
- ✅ Cambiar configuración **sin reiniciar servicios** (desde el Admin)
- ✅ Mantener credenciales **fuera del código** (en ENV para producción)
- ✅ Tener **valores por defecto** seguros

---

## Servicios Configurables

### 1. Teams/Azure AD

**Campos en Configuracion:**
- `teams_tenant_id` → Fallback a `TEAMS_TENANT` (ENV)
- `teams_client_id` → Fallback a `TEAMS_CLIENT_ID` (ENV)
- `teams_client_secret` → Fallback a `TEAMS_CLIENT_SECRET` (ENV)

**Ubicación del código:**
- `src/alumnos/services/teams_service.py:46-54`

```python
def __init__(self):
    from ..models import Configuracion
    config = Configuracion.load()

    # Fallback: Configuracion DB → ENV
    self.tenant = config.teams_tenant_id or settings.TEAMS_TENANT
    self.client_id = config.teams_client_id or settings.TEAMS_CLIENT_ID
    self.client_secret = config.teams_client_secret or settings.TEAMS_CLIENT_SECRET
```

---

### 2. Moodle

**Campos en Configuracion:**
- `moodle_base_url` → Fallback a `MOODLE_BASE_URL` (ENV)
- `moodle_wstoken` → Fallback a `MOODLE_WSTOKEN` (ENV)

**Ubicación del código:**
- Pendiente de implementar en `MoodleService.__init__()`

**Código recomendado:**
```python
def __init__(self):
    from ..models import Configuracion
    config = Configuracion.load()

    self.base_url = config.moodle_base_url or settings.MOODLE_BASE_URL
    self.wstoken = config.moodle_wstoken or settings.MOODLE_WSTOKEN
```

---

### 3. Email (SMTP)

**Campos en Configuracion:**
- `email_from` → Fallback a `DEFAULT_FROM_EMAIL` (ENV)
- `email_host` → Fallback a `EMAIL_HOST` (ENV)
- `email_port` → Fallback a `EMAIL_PORT` (ENV)
- `email_use_tls` → Fallback a `EMAIL_USE_TLS` (ENV)

**Ubicación del código:**
- `src/alumnos/services/email_service.py:37-45`

```python
def __init__(self):
    from ..models import Configuracion
    config = Configuracion.load()

    self.from_email = config.email_from or settings.DEFAULT_FROM_EMAIL
    self.email_host = config.email_host or settings.EMAIL_HOST
    self.email_port = config.email_port if config.email_port is not None else settings.EMAIL_PORT
    self.email_use_tls = config.email_use_tls if config.email_use_tls is not None else settings.EMAIL_USE_TLS
```

**Nota:** Para campos booleanos o numéricos, usar `is not None` en vez de `or` para evitar que `False` o `0` sean interpretados como vacíos.

---

## Cómo Funciona el Fallback

### Ejemplo: Teams Tenant ID

**Escenario 1: Campo vacío en DB**

```
Admin: teams_tenant_id = "" (vacío)
ENV:   TEAMS_TENANT = "1f7d4699-ccd7-45d6-b..."

TeamsService lee:
→ config.teams_tenant_id = ""
→ Es falsy (evaluates to False)
→ Usa settings.TEAMS_TENANT
→ Resultado: "1f7d4699-ccd7-45d6-b..."
```

**Escenario 2: Campo lleno en DB**

```
Admin: teams_tenant_id = "AAAA-BBBB-CCCC-DDDD"
ENV:   TEAMS_TENANT = "1f7d4699-ccd7-45d6-b..."

TeamsService lee:
→ config.teams_tenant_id = "AAAA-BBBB-CCCC-DDDD"
→ Es truthy (tiene valor)
→ Usa config.teams_tenant_id
→ Resultado: "AAAA-BBBB-CCCC-DDDD"
```

---

## Cuándo Usar DB vs ENV

### Usar Configuración en DB (Admin)

**Casos:**
- Entorno de **testing/desarrollo** donde las credenciales cambian frecuentemente
- Quieres poder cambiar configuración **sin reiniciar containers**
- Tienes **múltiples entornos** (dev, staging, prod) compartiendo misma imagen Docker

**Ventajas:**
- ✅ Cambios **inmediatos** (sin reiniciar)
- ✅ Visible en el **Admin de Django**
- ✅ Trazabilidad (campo `actualizado_por`)

**Desventajas:**
- ⚠️ Credenciales almacenadas en **base de datos** (menos seguro que ENV)
- ⚠️ Requiere **backup** de la base de datos para recuperar configuración

---

### Usar Variables de Entorno (ENV)

**Casos:**
- Entorno de **producción** donde la seguridad es crítica
- Despliegues en **cloud** (AWS, Azure, GCP) con gestión de secretos
- Configuración que **no debe cambiar** (ej: tenant ID)

**Ventajas:**
- ✅ **Más seguro** (secretos fuera de la BD)
- ✅ Compatible con **gestores de secretos** (AWS Secrets Manager, Azure Key Vault, etc.)
- ✅ Backups **no contienen credenciales**

**Desventajas:**
- ⚠️ Cambios requieren **reiniciar servicios**
- ⚠️ No visible desde el **Admin**

---

## Flujo de Configuración Recomendado

### Desarrollo

```
1. Dejar campos vacíos en Admin
2. Configurar en .env.dev:
   TEAMS_TENANT=...
   TEAMS_CLIENT_ID=...
   EMAIL_HOST=mailhog
   ...
3. Docker Compose carga automáticamente .env.dev
```

---

### Testing/Staging

```
1. Llenar campos en Admin para cada entorno
2. Dejar .env.staging con valores por defecto
3. Cada tester puede sobrescribir desde Admin sin afectar a otros
```

---

### Producción

```
1. Dejar campos vacíos en Admin (no almacenar credenciales en BD)
2. Configurar secretos en:
   - AWS Secrets Manager
   - Azure Key Vault
   - Kubernetes Secrets
   - Docker Swarm Secrets
3. Inyectar como variables de entorno al iniciar containers
```

---

## Acceso desde el Admin

**URL:** http://localhost:8000/admin/alumnos/configuracion/

**Fieldsets:**

### 🔐 Credenciales Teams/Azure AD (colapsado por defecto)
- Teams tenant id
- Teams client id
- Teams client secret

### 🎓 Credenciales Moodle (colapsado por defecto)
- Moodle base url
- Moodle wstoken

### 📧 Configuración de Email (colapsado por defecto)
- Email from
- Email host
- Email port
- Email use tls

**Nota:** Todos los fieldsets están colapsados por defecto para evitar exposición accidental de credenciales.

---

## Testing del Fallback

### Verificar que lee de ENV cuando DB está vacío

```bash
docker compose -f docker-compose.dev.yml exec web python manage.py shell
```

```python
from alumnos.models import Configuracion
from alumnos.services.teams_service import TeamsService

config = Configuracion.load()
print(f"DB teams_tenant_id: {config.teams_tenant_id or '(vacío)'}")

ts = TeamsService()
print(f"TeamsService tenant: {ts.tenant[:20]}...")
# Debería mostrar el valor de ENV
```

### Verificar que prioriza DB cuando tiene valor

```python
config.teams_tenant_id = "TEST-TENANT-ID"
config.save()

ts = TeamsService()
print(f"TeamsService tenant: {ts.tenant}")
# Debería mostrar "TEST-TENANT-ID"
```

---

## Migración Aplicada

**Archivo:** `alumnos/migrations/0008_add_email_config_fields.py`

**Campos agregados:**
- `Configuracion.email_from` (EmailField, blank=True)
- `Configuracion.email_host` (CharField, blank=True)
- `Configuracion.email_port` (PositiveIntegerField, null=True, blank=True)
- `Configuracion.email_use_tls` (BooleanField, null=True, blank=True)

**Comandos ejecutados:**
```bash
docker compose -f docker-compose.dev.yml exec web python manage.py makemigrations alumnos -n add_email_config_fields
docker compose -f docker-compose.dev.yml exec web python manage.py migrate alumnos
docker compose -f docker-compose.dev.yml restart celery celery-beat web
```

---

## Orden de Prioridad

Para todos los servicios, el orden de prioridad es:

```
1. Configuracion DB (si tiene valor)
   ↓ (si está vacío)
2. Variables de Entorno (.env)
   ↓ (si no existe)
3. Defaults hardcodeados en settings.py
```

---

## Troubleshooting

### Error: "NoneType has no attribute..."

**Causa:** Tanto DB como ENV están vacíos

**Solución:**
```bash
# Verificar variables de entorno
docker compose -f docker-compose.dev.yml exec web env | grep TEAMS

# Si no existen, agregar a .env.dev
echo "TEAMS_TENANT=tu-tenant-id" >> .env.dev
docker compose -f docker-compose.dev.yml restart web celery
```

---

### Cambios en Admin no se reflejan

**Causa:** Services instanciados antes del cambio

**Solución:**
```bash
# Los servicios leen config en __init__()
# Reiniciar workers para que re-instancien:
docker compose -f docker-compose.dev.yml restart celery celery-beat web
```

**Nota:** En el futuro, considerar implementar cache invalidation o reload automático de configuración.

---

### ¿Cómo saber de dónde está leyendo?

Agregar logging temporal en los servicios:

```python
def __init__(self):
    config = Configuracion.load()

    self.tenant = config.teams_tenant_id or settings.TEAMS_TENANT

    # Logging para debugging
    if config.teams_tenant_id:
        logger.info(f"TeamsService: usando tenant de DB")
    else:
        logger.info(f"TeamsService: usando tenant de ENV")
```

Luego revisar logs:
```bash
docker logs pylucy-celery-dev | grep "TeamsService"
```

---

**Última actualización**: 2025-12-11
**Versión**: 1.0
