# Configuración del Sistema PyLucy

## Gestión de Configuración con JSON

El sistema permite exportar e importar toda la configuración en formato JSON para facilitar el traspaso entre entornos.

### Comandos Disponibles

#### Exportar Configuración

```bash
# Exportar configuración actual a JSON
docker compose -f docker-compose.testing.yml exec web python manage.py config export --file /app/config.json

# Copiar el archivo del contenedor al host
docker cp pylucy-web-testing:/app/config.json ./configuracion_backup.json
```

#### Importar Configuración

```bash
# 1. Copiar archivo JSON al contenedor
docker cp configuracion_real.json pylucy-web-testing:/app/configuracion_real.json

# 2. Importar configuración desde JSON
docker compose -f docker-compose.testing.yml exec web python manage.py config import --file /app/configuracion_real.json

# 3. Verificar que se importó correctamente
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "from alumnos.models import Configuracion; c = Configuracion.load(); print(f'✅ Teams Tenant: {c.teams_tenant_id}'); print(f'✅ Moodle: {c.moodle_base_url}'); print(f'✅ SIAL: {c.sial_base_url}')"
```

### Archivo de Configuración JSON

El archivo `configuracion_real.json` contiene:

```json
{
  "batch_size": 20,
  "rate_limit_teams": 10,
  "rate_limit_moodle": 30,

  "teams_tenant_id": "1f7d4699-ccd7-45d6-bc78-b8b950bcaedc",
  "teams_client_id": "138e98af-33e5-439c-9981-3caaedc65c70",
  "teams_client_secret": "VE~8Q~SbnnIUg-iEHnr1m8nxu5J0RAskpLJPlbuU",
  "account_prefix": "test-a",

  "sial_base_url": "https://sisinfo.unrc.edu.ar",
  "sial_basic_user": "SIAL04_565",
  "sial_basic_pass": "pos15MAL@kapri",

  "moodle_base_url": "https://v.eco.unrc.edu.ar",
  "moodle_wstoken": "45fba879dcddc17a16436ac156cb880e",
  "moodle_email_type": "institucional",
  "moodle_student_roleid": 5,
  "moodle_auth_method": "oauth2",

  "email_plantilla_bienvenida": "<!DOCTYPE html>...",
  "email_plantilla_credenciales": "<!DOCTYPE html>...",
  "email_plantilla_password": "<!DOCTYPE html>...",

  "email_from": "no-reply@eco.unrc.edu.ar",
  "email_host": "mailhog",
  "email_port": 1025,
  "email_use_tls": false
}
```

## Credenciales Actuales (Testing)

### Teams/Azure AD
- **Tenant ID**: `1f7d4699-ccd7-45d6-bc78-b8b950bcaedc`
- **Client ID**: `138e98af-33e5-439c-9981-3caaedc65c70`
- **Client Secret**: `VE~8Q~SbnnIUg-iEHnr1m8nxu5J0RAskpLJPlbuU`
- **Domain**: `eco.unrc.edu.ar`
- **Prefijo cuentas**: `test-a` (testing) / `a` (producción)

### SIAL/UTI
- **URL**: `https://sisinfo.unrc.edu.ar`
- **Usuario**: `SIAL04_565`
- **Password**: `pos15MAL@kapri`

### Moodle
- **URL**: `https://v.eco.unrc.edu.ar`
- **Token**: `45fba879dcddc17a16436ac156cb880e`
- **Email Type**: `institucional`
- **Student Role ID**: `5`
- **Auth Method**: `oauth2` (Microsoft Teams)

### Email (MailHog para testing)
- **Host**: `mailhog`
- **Port**: `1025`
- **TLS**: `False`
- **From**: `no-reply@eco.unrc.edu.ar`

## Flujo Completo de Configuración

### En el servidor donde corre la aplicación:

```bash
# 1. Clonar/actualizar repositorio
git pull origin main

# 2. El archivo configuracion_real.json ya está en el repo

# 3. Copiar al contenedor e importar
docker cp configuracion_real.json pylucy-web-testing:/app/configuracion_real.json
docker compose -f docker-compose.testing.yml exec web python manage.py config import --file /app/configuracion_real.json

# 4. Verificar
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Configuracion
c = Configuracion.load()
print(f'Teams: {c.teams_tenant_id}')
print(f'Moodle: {c.moodle_base_url}')
print(f'SIAL: {c.sial_base_url}')
print(f'Plantillas cargadas: {len(c.email_plantilla_bienvenida)>0}')
"
```

## Variables de Entorno vs Base de Datos

**IMPORTANTE**: El sistema usa un sistema híbrido:

1. **Variables de Entorno (`.env.testing.real`)**:
   - Configuración de infraestructura (DB, Redis, Celery)
   - Valores de fallback si no hay configuración en BD

2. **Base de Datos (modelo `Configuracion`)**:
   - Configuración dinámica editable desde admin
   - Credenciales de servicios externos (Teams, Moodle, SIAL)
   - Plantillas de emails
   - Rate limits y batch sizes

**Orden de prioridad**: Base de Datos > Variables de Entorno > Default hardcoded

## Modificar Configuración

### Opción 1: Via Admin Django
1. Ir a `/admin/alumnos/configuracion/`
2. Editar los campos necesarios
3. Guardar

### Opción 2: Via JSON
1. Exportar configuración actual
2. Editar el archivo JSON
3. Importar de nuevo

### Opción 3: Via Shell
```python
from alumnos.models import Configuracion
c = Configuracion.load()
c.batch_size = 50
c.rate_limit_teams = 20
c.save()
```

## Troubleshooting

### "Archivo no encontrado" al importar
Asegúrate de copiar el archivo al contenedor primero:
```bash
docker cp configuracion_real.json pylucy-web-testing:/app/
```

### Configuración no se aplica
Verifica que solo existe un registro de Configuracion:
```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Configuracion
print(f'Registros: {Configuracion.objects.count()}')
"
```

### Credenciales no funcionan
Verifica en admin que los valores se guardaron correctamente:
```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.models import Configuracion
c = Configuracion.load()
print(f'SIAL URL: {c.sial_base_url}')
print(f'SIAL User: {c.sial_basic_user}')
print(f'Teams Tenant: {c.teams_tenant_id}')
"
```
