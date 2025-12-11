# Configurar Teams y Email en PyLucy

## ✅ Sí, puedes cambiar Teams y Email desde el Admin

PyLucy permite configurar Teams y Email de **dos formas**:

1. **Desde el Django Admin** (Recomendado) ✅
2. Desde variables de entorno (Respaldo)

---

## 🎯 Configurar desde Django Admin

### Paso 1: Acceder a Configuración del Sistema

1. Ir a: `http://IP_SERVIDOR:8000/admin/`
2. Login con: `AdminFCE.16` / `Milei2027!` (o `admin` / `admin`)
3. En el menú lateral: **Alumnos** → **Configuración del Sistema**
4. Click en la única configuración existente (se crea automáticamente)

### Paso 2: Configurar Teams

En la sección **"🔐 Credenciales Teams/Azure AD"** (expandir):

```
┌─────────────────────────────────────────────────────────┐
│ 🔐 Credenciales Teams/Azure AD                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Teams tenant id:                                        │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx                │ │
│ └─────────────────────────────────────────────────────┘ │
│ Tenant ID de Azure AD (GUID). Si está vacío, usa      │
│ variable de entorno                                      │
│                                                          │
│ Teams client id:                                        │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy                │ │
│ └─────────────────────────────────────────────────────┘ │
│ Client ID de Teams App. Si está vacío, usa variable   │
│ de entorno                                               │
│                                                          │
│ Teams client secret:                                    │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ abc123def456ghi789jkl012mno345pqr678                │ │
│ └─────────────────────────────────────────────────────┘ │
│ Client Secret de Teams App. Si está vacío, usa        │
│ variable de entorno                                      │
│                                                          │
│ Account prefix:                                         │
│ ┌──────────┐                                            │
│ │  test-a  │  ← "test-a" para testing, "a" para prod  │
│ └──────────┘                                            │
│ Prefijo para cuentas (ej: 'test-a' para testing, 'a'  │
│ para producción). Si está vacío, usa variable de       │
│ entorno                                                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Paso 3: Configurar Email

En la sección **"📧 Configuración de Email"** (expandir):

```
┌─────────────────────────────────────────────────────────┐
│ 📧 Configuración de Email                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Email from:                                             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ no-reply@eco.unrc.edu.ar                            │ │
│ └─────────────────────────────────────────────────────┘ │
│ Email remitente para notificaciones. Si está vacío,   │
│ usa DEFAULT_FROM_EMAIL de entorno                       │
│                                                          │
│ Email host:                                             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ mailhog                                             │ │
│ └─────────────────────────────────────────────────────┘ │
│ Servidor SMTP para envío de emails. Si está vacío,    │
│ usa EMAIL_HOST de entorno                               │
│                                                          │
│ Email port:                                             │
│ ┌──────┐                                                │
│ │ 1025 │                                               │
│ └──────┘                                                │
│ Puerto SMTP (ej: 587 para TLS, 465 para SSL). Si      │
│ está vacío, usa EMAIL_PORT de entorno                   │
│                                                          │
│ Email use tls:                                          │
│ ☐ Activado                                             │
│ Usar TLS para conexión SMTP. Si es NULL, usa          │
│ EMAIL_USE_TLS de entorno                                │
│                                                          │
└─────────────────────────────────────────────────────────┘

              [ Guardar ]  [ Guardar y continuar editando ]
```

### Paso 4: Guardar y Reiniciar (Opcional)

Los cambios se aplican **inmediatamente** (no requiere reiniciar).

Si quieres asegurarte:
```bash
docker compose -f docker-compose.testing.yml restart celery
```

---

## 🔧 Valores Recomendados por Ambiente

### Para TESTING ALFA (Actual):
```
Teams tenant id: (tenant de testing)
Teams client id: (client id de testing)
Teams client secret: (secret de testing)
Account prefix: test-a  ← IMPORTANTE para testing

Email from: no-reply@eco.unrc.edu.ar
Email host: mailhog  ← MailHog captura emails
Email port: 1025
Email use tls: ☐ No (MailHog no usa TLS)
```

**Resultado:**
- Crea usuarios: `test-a12345678@eco.unrc.edu.ar`
- Emails van a MailHog (ver en http://IP:8025)
- NO se envían emails reales

### Para TESTING REAL:
```
Teams tenant id: (tenant real)
Teams client id: (client id real)
Teams client secret: (secret real)
Account prefix: a  ← Prefijo de producción

Email from: no-reply@eco.unrc.edu.ar
Email host: mailhog  ← AÚN MailHog (seguridad)
Email port: 1025
Email use tls: ☐ No
```

**Resultado:**
- Crea usuarios REALES: `a12345678@eco.unrc.edu.ar`
- Emails van a MailHog (NO a estudiantes)
- Permite probar con datos reales sin riesgo

### Para PRODUCCIÓN:
```
Teams tenant id: (tenant real)
Teams client id: (client id real)
Teams client secret: (secret real)
Account prefix: a

Email from: no-reply@eco.unrc.edu.ar
Email host: smtp.eco.unrc.edu.ar  ← SMTP REAL
Email port: 587
Email use tls: ☑ Sí
```

**Resultado:**
- Crea usuarios REALES: `a12345678@eco.unrc.edu.ar`
- **ENVÍA EMAILS REALES** a estudiantes ⚠️

---

## 🔄 Orden de Prioridad

PyLucy busca la configuración en este orden:

```
1. Base de Datos (Django Admin)
   ↓ (si no existe o está vacío)
2. Variables de Entorno (.env.dev)
   ↓ (si no existe)
3. Default hardcodeado
```

### Ejemplo para Teams Tenant:

```python
# En Django Admin:
Teams tenant id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  ← USAR ESTE

# En .env.dev:
TEAMS_TENANT=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy     ← Ignorado

# Resultado: Usa xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Ejemplo para Account Prefix:

```python
# En Django Admin:
Account prefix: test-a  ← USAR ESTE

# En .env.dev:
ACCOUNT_PREFIX=a        ← Ignorado

# Resultado: Crea usuarios test-a12345678@eco.unrc.edu.ar
```

### Ejemplo para Email Host:

```python
# En Django Admin:
Email host: mailhog  ← USAR ESTE

# En .env.dev:
EMAIL_HOST=smtp.eco.unrc.edu.ar  ← Ignorado

# Resultado: Emails van a MailHog (no a SMTP real)
```

---

## 🔑 Cómo Obtener Credenciales de Teams

### Paso 1: Registrar App en Azure Portal

1. Ir a: https://portal.azure.com
2. **Azure Active Directory** → **App registrations** → **New registration**
3. Datos:
   - Nombre: `PyLucy Integration`
   - Supported account types: `Accounts in this organizational directory only`
   - Redirect URI: (dejar vacío)
4. Click **Register**

### Paso 2: Obtener Client ID y Tenant ID

Después de registrar la app:
- **Application (client) ID**: Este es tu `teams_client_id`
- **Directory (tenant) ID**: Este es tu `teams_tenant_id`

### Paso 3: Generar Client Secret

1. En la app registrada → **Certificates & secrets**
2. **New client secret**
3. Description: `PyLucy Secret`
4. Expires: 24 months (o lo que requiera la org)
5. Click **Add**
6. **COPIAR EL VALUE INMEDIATAMENTE** (no se vuelve a mostrar)
7. Este es tu `teams_client_secret`

### Paso 4: Asignar Permisos

1. En la app → **API permissions**
2. **Add a permission** → **Microsoft Graph** → **Application permissions**
3. Buscar y agregar:
   - `User.ReadWrite.All` (crear/modificar usuarios)
   - `Directory.ReadWrite.All` (acceso al directorio)
4. Click **Add permissions**
5. **IMPORTANTE**: Click en **Grant admin consent** (requiere admin global)

### Paso 5: Configurar en PyLucy

Pegar los valores en Django Admin → Configuración:
- `teams_tenant_id`: Directory (tenant) ID
- `teams_client_id`: Application (client) ID
- `teams_client_secret`: Secret Value (el que copiaste)

---

## 🧪 Probar la Configuración

### Desde Django Admin:

1. Ir a **Alumnos** → **Alumnos**
2. Seleccionar un alumno de prueba
3. Click en **Actions** → **🚀 Activar Teams + Enviar Email**
4. Ver logs en **Tareas Asíncronas** y **Logs de Sistema**

### Desde Terminal (ver configuración actual):

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.utils.config import (
    get_teams_tenant,
    get_teams_client_id,
    get_account_prefix,
    get_email_host,
    get_email_port
)
print('Teams Tenant:', get_teams_tenant()[:20] + '...' if get_teams_tenant() else 'No configurado')
print('Teams Client ID:', get_teams_client_id()[:20] + '...' if get_teams_client_id() else 'No configurado')
print('Account Prefix:', get_account_prefix())
print('Email Host:', get_email_host())
print('Email Port:', get_email_port())
"
```

### Ver emails capturados (MailHog):

```bash
# Abrir en navegador:
http://IP_SERVIDOR:8025
```

### Logs de Celery:

```bash
# Ver si se conecta a Teams
docker compose -f docker-compose.testing.yml logs -f celery | grep -i teams

# Ver si envía emails
docker compose -f docker-compose.testing.yml logs -f celery | grep -i email
```

---

## 📊 Diferencia entre Testing y Producción

| Aspecto | TESTING ALFA | TESTING REAL | PRODUCCIÓN |
|---------|--------------|--------------|------------|
| **Account Prefix** | `test-a` | `a` | `a` |
| **Usuarios creados** | `test-a12345@eco...` | `a12345@eco...` | `a12345@eco...` |
| **Teams Tenant** | Testing (si existe) | Real | Real |
| **Email Host** | `mailhog` | `mailhog` | `smtp.eco.unrc.edu.ar` |
| **Email Port** | `1025` | `1025` | `587` |
| **Email TLS** | No | No | Sí |
| **Emails enviados** | ❌ Capturados | ❌ Capturados | ✅ **REALES** |

---

## 🛡️ Seguridad

### ⚠️ Las credenciales de Teams son MUY SENSIBLES:

- ✅ Guardarlo en la base de datos (Django Admin) está OK
- ✅ La base de datos está protegida
- ❌ NO compartir las credenciales
- ❌ NO exponerlas en logs públicos
- ❌ NO subirlas a Git (si las pones en .env.prod)

### Rotar credenciales:

Si las credenciales se comprometen:
1. Ir a Azure Portal → App registrations → tu app
2. **Certificates & secrets** → Eliminar el secret viejo
3. Crear un nuevo secret
4. Actualizar en Django Admin → Configuración

### Email Host (MailHog vs SMTP Real):

**En TESTING (MailHog):**
- ✅ Captura todos los emails
- ✅ NO envía nada a estudiantes
- ✅ Puedes ver emails en http://IP:8025
- ✅ Perfecto para testing

**En PRODUCCIÓN (SMTP Real):**
- ⚠️ **ENVÍA EMAILS REALES** a estudiantes
- ⚠️ Requiere credenciales de SMTP
- ⚠️ Verificar SIEMPRE antes de enviar
- ⚠️ Tener plan de rollback

---

## 📋 Checklist de Verificación

### Antes de TESTING ALFA:
- [ ] Configurar `account_prefix: test-a`
- [ ] Configurar `email_host: mailhog`
- [ ] Configurar `email_port: 1025`
- [ ] Email TLS: Desactivado
- [ ] Probar con 1 alumno de prueba
- [ ] Verificar en MailHog que el email se capturó
- [ ] Verificar que el usuario creado tiene prefijo `test-a`

### Antes de TESTING REAL:
- [ ] Obtener credenciales reales de Teams
- [ ] Configurar `account_prefix: a` en admin
- [ ] Mantener `email_host: mailhog` (seguridad)
- [ ] Probar con 1 alumno real
- [ ] Verificar que crea usuario `a12345@eco...`
- [ ] Verificar email en MailHog (NO enviado)
- [ ] Hacer backup de base de datos

### Antes de PRODUCCIÓN:
- [ ] Testing real completado exitosamente
- [ ] Cambiar `email_host: smtp.eco.unrc.edu.ar`
- [ ] Cambiar `email_port: 587`
- [ ] Activar Email TLS
- [ ] Obtener credenciales SMTP reales
- [ ] Probar con 1 alumno de prueba en horario controlado
- [ ] Configurar monitoreo de emails enviados
- [ ] Plan de rollback documentado

---

## 🆘 Troubleshooting

### "No puedo ver las credenciales de Teams en el admin"
- Expandir la sección "🔐 Credenciales Teams/Azure AD"
- Verificar que tengas permisos de superuser

### "Los cambios no se aplican"
- Los cambios son inmediatos
- Si procesaste antes de cambiar, las tareas en cola usan config vieja
- Reinicia celery: `docker compose -f docker-compose.testing.yml restart celery`

### "Sigue usando el prefijo de .env.dev"
- Verificar que hayas guardado en Django Admin
- Verificar que el campo NO esté vacío
- Usar comando de terminal arriba para ver qué prefijo está usando

### "Emails van a estudiantes en testing"
- **VERIFICAR** que `email_host` sea `mailhog`
- **NUNCA** usar `smtp.eco.unrc.edu.ar` en testing
- Abrir http://IP:8025 para confirmar que MailHog captura

### "Error de autenticación con Teams"
- Verificar que el Tenant ID sea correcto
- Verificar que el Client Secret no haya expirado
- Verificar que se haya dado "Grant admin consent" en Azure

---

## 🎯 Resumen

**Pregunta**: ¿Puedo cambiar Teams y Email desde la configuración?

**Respuesta**: ✅ **SÍ**

**Dónde**: Django Admin → Alumnos → Configuración del Sistema

**Requiere reiniciar**: ❌ NO (los cambios se aplican inmediatamente)

**Tiene prioridad sobre .env.dev**: ✅ SÍ

**Es la forma recomendada**: ✅ SÍ

**IMPORTANTE para testing**: Siempre usar:
- `account_prefix: test-a`
- `email_host: mailhog`
- `email_port: 1025`

Esto asegura que:
- ✅ NO se crean usuarios reales en producción
- ✅ NO se envían emails a estudiantes
- ✅ Todo se captura en MailHog para verificación
