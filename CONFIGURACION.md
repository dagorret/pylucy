# Configuración de PyLucy

Este documento explica cómo configurar PyLucy para desarrollo y producción, especialmente respecto a las **credenciales de servicios externos**.

## 📋 Tabla de Contenidos

- [Requisitos Previos](#requisitos-previos)
- [Configuración Inicial](#configuración-inicial)
- [Credenciales de Servicios](#credenciales-de-servicios)
- [Variables de Entorno](#variables-de-entorno)
- [Modo Testing vs Producción](#modo-testing-vs-producción)
- [Seguridad](#seguridad)

---

## Requisitos Previos

- Docker y Docker Compose instalados
- Python 3.12+ (para desarrollo local sin Docker)
- PostgreSQL 16
- Redis 7

## Configuración Inicial

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/pylucy.git
cd pylucy
```

### 2. Configurar Variables de Entorno

Copia el archivo de ejemplo y edítalo con tus valores:

```bash
cp .env.example .env.dev
nano .env.dev
```

Genera una `DJANGO_SECRET_KEY` segura:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Configurar Credenciales de Servicios

PyLucy se integra con tres servicios externos que requieren credenciales:

1. **UTI/SIAL**: Sistema de Información Académica UNRC
2. **Moodle**: Plataforma de Aprendizaje Virtual
3. **Microsoft Teams**: Gestión de usuarios y grupos

Las credenciales se almacenan en archivos JSON en la carpeta `credenciales/` (que está excluida de Git por seguridad).

#### Configurar UTI/SIAL

```bash
cd credenciales/
cp uti_credentials.json.example uti_credentials.json
nano uti_credentials.json
```

Edita el archivo con las credenciales proporcionadas por el administrador de UTI:

```json
{
  "base_url": "https://sisinfo.unrc.edu.ar",
  "basic_auth": {
    "username": "TU_USUARIO_UTI",
    "password": "TU_PASSWORD_UTI"
  },
  "environment": "production"
}
```

#### Configurar Moodle

```bash
cp moodle_credentials.json.example moodle_credentials.json
nano moodle_credentials.json
```

Necesitas generar un token de Web Services en Moodle:

1. Inicia sesión como administrador en Moodle
2. Ve a: **Administración del sitio > Plugins > Servicios web > Gestionar tokens**
3. Crea un token para el usuario de integración
4. Copia el token al archivo JSON:

```json
{
  "base_url": "https://tu-moodle.ejemplo.com",
  "wstoken": "TU_TOKEN_MOODLE_AQUI",
  "student_roleid": 5,
  "auth_method": "oauth2"
}
```

#### Configurar Microsoft Teams

```bash
cp teams_credentials.json.example teams_credentials.json
nano teams_credentials.json
```

Necesitas crear una App Registration en Azure Portal:

1. Ve a [Azure Portal](https://portal.azure.com)
2. **Azure Active Directory > App registrations > New registration**
3. Configura permisos API: `User.ReadWrite.All`, `Directory.ReadWrite.All`
4. Crea un Client Secret en **Certificates & secrets**
5. Copia los valores al archivo JSON:

```json
{
  "tenant_id": "TU_AZURE_TENANT_ID",
  "domain": "tu-dominio.ejemplo.com",
  "client_id": "TU_CLIENT_ID",
  "client_secret": "TU_CLIENT_SECRET"
}
```

### 4. Establecer Permisos Seguros

```bash
chmod 600 credenciales/*.json
```

Esto asegura que solo el propietario pueda leer/escribir las credenciales.

### 5. Iniciar el Proyecto

```bash
# Con Docker Compose (recomendado)
./deploy-testing.sh start

# O manualmente
docker compose -f docker-compose.testing.yml up -d
```

---

## Credenciales de Servicios

### Jerarquía de Carga

PyLucy busca credenciales en el siguiente orden:

1. **Base de datos** (modelo `Configuracion`)
2. **Archivos JSON** en `credenciales/`
3. **Variables de entorno** (fallback)
4. **Valores por defecto** (desarrollo)

### Fallback a Variables de Entorno

Si prefieres usar variables de entorno en lugar de archivos JSON, puedes configurarlas en `.env.dev`:

```bash
# UTI/SIAL
SIAL_BASE_URL=https://sisinfo.unrc.edu.ar
SIAL_BASIC_USER=tu_usuario
SIAL_BASIC_PASS=tu_password

# Moodle
MOODLE_BASE_URL=https://tu-moodle.ejemplo.com
MOODLE_WSTOKEN=tu_token

# Teams
TEAMS_TENANT=tu-tenant-id
TEAMS_DOMAIN=tu-dominio.com
TEAMS_CLIENT_ID=tu-client-id
TEAMS_CLIENT_SECRET=tu-client-secret
```

---

## Modo Testing vs Producción

PyLucy puede ejecutarse en dos modos:

### Modo Testing

```bash
ENVIRONMENT_MODE=testing
ACCOUNT_PREFIX=test-a
```

- Cuentas con prefijo: `test-a12345678@eco.unrc.edu.ar`
- Usa Moodle sandbox o entorno de pruebas
- Logs más verbosos
- MailHog para capturar emails

### Modo Producción

```bash
ENVIRONMENT_MODE=production
ACCOUNT_PREFIX=a
```

- Cuentas sin prefijo de prueba: `a12345678@eco.unrc.edu.ar`
- Usa Moodle y Teams de producción
- SMTP real (Office 365)
- Logs controlados

---

## Seguridad

### ✅ Buenas Prácticas

- ✅ **Nunca** subas archivos con credenciales a Git
- ✅ Usa la carpeta `credenciales/` para datos sensibles
- ✅ Rota credenciales periódicamente
- ✅ Usa permisos 600 en archivos de credenciales
- ✅ En producción, considera usar:
  - Azure Key Vault
  - AWS Secrets Manager
  - HashiCorp Vault

### ⚠️ Qué NO hacer

- ❌ NO hardcodees credenciales en el código
- ❌ NO compartas credenciales por email/chat sin cifrar
- ❌ NO uses las mismas credenciales en testing y producción
- ❌ NO subas archivos `.env` o `credenciales/*.json` a Git

### Archivos Excluidos de Git

El `.gitignore` excluye automáticamente:

```
# Variables de entorno
.env
.env.*
!.env.*.example

# Credenciales JSON
credenciales/*.json
!credenciales/*.json.example
```

---

## Verificación

Para verificar que tu configuración es correcta:

```bash
# Verificar variables de entorno
./deploy-testing.sh shell
python manage.py check_environment

# Verificar credenciales de servicios
python manage.py shell
>>> from pylucy.credentials_loader import get_uti_credentials, get_moodle_credentials, get_teams_credentials
>>> print(get_uti_credentials())
>>> print(get_moodle_credentials())
>>> print(get_teams_credentials())
```

---

## Soporte

Si tienes problemas con la configuración:

1. Revisa los logs: `./deploy-testing.sh logs`
2. Verifica permisos de archivos: `ls -la credenciales/`
3. Consulta la documentación del servicio específico
4. Abre un issue en GitHub (sin incluir credenciales)

---

**Autor:** Carlos Dagorret
**Licencia:** MIT
**Última actualización:** 2025-12-29
