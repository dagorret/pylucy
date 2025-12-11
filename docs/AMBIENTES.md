# Ambientes de PyLucy - Configuración Detallada

## 📊 Resumen de Ambientes

PyLucy tiene 3 configuraciones principales:

| Componente | DESARROLLO LOCAL | TESTING ALFA (Actual) | TESTING REAL | PRODUCCIÓN |
|------------|------------------|----------------------|--------------|------------|
| **Django DEBUG** | ✅ True | ✅ True | ⚠️ False | ❌ False |
| **SIAL/UTI API** | 🧪 Mock | 🧪 Mock | 🌐 **API Real UTI** | 🌐 **API Real UTI** |
| **Moodle** | 🧪 Sandbox | 🧪 Sandbox | 🌐 **Moodle Real** | 🌐 **Moodle Real** |
| **Teams** | 🧪 Test (test-a) | 🧪 Test (test-a) | 🌐 **Real (a)** | 🌐 **Real (a)** |
| **Email/SMTP** | 📧 MailHog | 📧 MailHog | 📧 **MailHog** | 📬 **SMTP Real** |
| **Base de Datos** | 🗄️ PostgreSQL local | 🗄️ PostgreSQL Docker | 🗄️ PostgreSQL Docker | 🗄️ PostgreSQL Docker |
| **Servidor Web** | 🐍 runserver | 🐍 runserver | 🐍 runserver | 🦄 Gunicorn + Nginx |
| **Archivos estáticos** | Django | Django | Django | Nginx |

---

## 🎯 Configuraciones Detalladas

### 1️⃣ DESARROLLO LOCAL (tu máquina)

**Archivo**: `.env.dev.local`
**Docker Compose**: `docker-compose.dev.yml`

```bash
DJANGO_DEBUG=True
ENVIRONMENT_MODE=testing

# APIs
SIAL_BASE_URL=http://host.docker.internal:8088  # Mock local
MOODLE_BASE_URL=https://sandbox.moodledemo.net  # Sandbox público
TEAMS_TENANT=... # Testing tenant
ACCOUNT_PREFIX=test-a  # Cuentas de prueba

# Email
EMAIL_HOST=mailhog  # MailHog en Docker
EMAIL_PORT=1025
```

**Características:**
- ✅ Todo local en tu máquina
- ✅ Mock API corre fuera de Docker o en Docker separado
- ✅ MailHog captura emails
- ✅ Moodle Sandbox (datos de prueba públicos)
- ✅ Teams en modo testing (crea test-a12345)

---

### 2️⃣ TESTING ALFA (servidor actual - 179.43.116.154)

**Archivo**: `.env.dev`
**Docker Compose**: `docker-compose.testing.yml`

```bash
DJANGO_DEBUG=True
ENVIRONMENT_MODE=testing

# APIs
SIAL_BASE_URL=http://mock-api-uti:8000  # 🧪 Mock en Docker
MOODLE_BASE_URL=https://sandbox.moodledemo.net  # 🧪 Sandbox
TEAMS_TENANT=... # Testing tenant
ACCOUNT_PREFIX=test-a  # Cuentas de prueba

# Email
EMAIL_HOST=mailhog  # 📧 MailHog captura
EMAIL_PORT=1025
```

**Características:**
- ✅ Mock API de SIAL/UTI (datos ficticios)
- ✅ Moodle Sandbox (datos de prueba)
- ✅ Teams modo testing (prefijo test-a)
- ✅ **MailHog captura emails** (NO envía emails reales)
- ✅ DEBUG activado (mensajes de error detallados)

**¿Qué hace?**
- Consulta datos de preinscriptos del MOCK
- Crea usuarios test-a12345 en Teams
- "Envía" emails a MailHog (puedes verlos en http://IP:8025)
- Sincroniza con Moodle Sandbox (si está configurado)

---

### 3️⃣ TESTING REAL (para probar antes de producción)

**Archivo**: `.env.testing.real` → copiar a `.env.dev`
**Docker Compose**: `docker-compose.testing.yml`

```bash
DJANGO_DEBUG=True  # ⚠️ Aún con debug para troubleshooting
ENVIRONMENT_MODE=production  # ← Modo producción

# APIs
SIAL_BASE_URL=https://sial.unrc.edu.ar  # 🌐 API REAL UTI
SIAL_BASIC_USER=usuario_real
SIAL_BASIC_PASS=contraseña_real

MOODLE_BASE_URL=https://moodle.eco.unrc.edu.ar  # 🌐 Moodle REAL
MOODLE_WSTOKEN=token_real

TEAMS_TENANT=... # Tenant real
ACCOUNT_PREFIX=a  # 🌐 Cuentas REALES (a12345)

# Email
EMAIL_HOST=mailhog  # 📧 Aún MailHog (seguridad)
EMAIL_PORT=1025
```

**Características:**
- 🌐 **Consulta API REAL de UTI** (datos reales de preinscriptos)
- 🌐 **Moodle REAL de FCE** (si token configurado)
- 🌐 **Teams REAL** (crea cuentas a12345, a67890, etc.)
- 📧 **MailHog** (captura emails para verificar antes de enviar)
- ✅ DEBUG activado (para ver errores fácilmente)

**¿Qué hace?**
- ✅ Consulta preinscriptos reales desde UTI
- ✅ Crea usuarios REALES en Teams (a12345)
- ✅ Sincroniza con Moodle real (si configurado)
- ✅ **NO envía emails reales** (MailHog los captura)

**⚠️ CASI como producción, pero:**
- Emails van a MailHog (no a estudiantes reales)
- DEBUG activado (para detectar errores)

---

### 4️⃣ PRODUCCIÓN (futuro)

**Archivo**: `.env.prod`
**Docker Compose**: `docker-compose.prod.yml`

```bash
DJANGO_DEBUG=False  # ❌ Debug desactivado
ENVIRONMENT_MODE=production

# APIs
SIAL_BASE_URL=https://sial.unrc.edu.ar  # 🌐 API REAL UTI
SIAL_BASIC_USER=usuario_prod
SIAL_BASIC_PASS=contraseña_prod

MOODLE_BASE_URL=https://moodle.eco.unrc.edu.ar  # 🌐 Moodle REAL
MOODLE_WSTOKEN=token_prod

TEAMS_TENANT=... # Tenant producción
ACCOUNT_PREFIX=a  # Cuentas REALES

# Email
EMAIL_HOST=smtp.eco.unrc.edu.ar  # 📬 SMTP REAL
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=no-reply@eco.unrc.edu.ar
EMAIL_HOST_PASSWORD=contraseña_smtp
```

**Características:**
- 🌐 **API REAL de UTI**
- 🌐 **Moodle REAL**
- 🌐 **Teams REAL** (cuentas reales)
- 📬 **SMTP REAL** (envía emails a estudiantes)
- ❌ DEBUG desactivado (seguridad)
- 🦄 Gunicorn + Nginx (producción)

**¿Qué hace?**
- ✅ Consulta preinscriptos reales desde UTI
- ✅ Crea usuarios REALES en Teams
- ✅ Sincroniza con Moodle real
- ✅ **ENVÍA EMAILS REALES** a estudiantes

---

## 📧 Flujo de Emails por Ambiente

### DESARROLLO / TESTING ALFA (actual):
```
PyLucy → MailHog (captura)
         ↓
    http://IP:8025 (ves el email)
```
**NO llega a nadie real** ✅

### TESTING REAL:
```
PyLucy → MailHog (captura)
         ↓
    http://IP:8025 (verificas antes de producción)
```
**NO llega a nadie real** ✅

### PRODUCCIÓN:
```
PyLucy → SMTP eco.unrc.edu.ar → Email del estudiante
```
**SÍ llega al estudiante real** ⚠️

---

## 🔄 Transición Recomendada

### Paso 1: Alfa (ACTUAL) ✅
- Mock API
- Moodle Sandbox
- Teams test-a
- MailHog
- **Objetivo**: Probar funcionalidad básica

### Paso 2: Testing Real (PRÓXIMO)
```bash
# En el servidor
cp .env.testing.real .env.dev
# Editar credenciales reales
nano .env.dev
# Reiniciar
docker compose -f docker-compose.testing.yml restart web celery
```
- **API REAL UTI** ← Datos reales de preinscriptos
- **Moodle REAL** ← Sincronización real
- **Teams REAL** ← Crea usuarios reales (a12345)
- **MailHog** ← Emails van a MailHog (seguridad)
- **Objetivo**: Validar con datos reales sin enviar emails

### Paso 3: Producción (FINAL)
```bash
# Configurar .env.prod
cp .env.prod.example .env.prod
# Editar con credenciales de producción
nano .env.prod
# Usar docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d
```
- API REAL
- Moodle REAL
- Teams REAL
- **SMTP REAL** ← Envía emails a estudiantes
- **Objetivo**: Operación en vivo

---

## 🎯 Tu Pregunta Respondida

> "Testing real casi queda como producción. Consulta UTI, consulta Moodle, manda correos a MailHog?"

**Respuesta: ✅ EXACTO**

**TESTING REAL:**
- ✅ Consulta API REAL de UTI (preinscriptos reales)
- ✅ Consulta Moodle REAL (si token configurado)
- ✅ Crea usuarios REALES en Teams (a12345, a67890...)
- ✅ Manda correos a **MailHog** (NO a estudiantes)

**Diferencias con PRODUCCIÓN:**
1. **Emails**: Van a MailHog, no a estudiantes
2. **DEBUG**: Activado (más fácil detectar errores)
3. **Servidor**: runserver (no Gunicorn+Nginx)

**¿Por qué es útil?**
- Pruebas con datos REALES sin riesgo
- Ves emails generados sin enviarlos
- Validas integración completa
- Detectas errores antes de producción

---

## 🛡️ Seguridad

### En TESTING REAL:
- ✅ Datos reales de UTI (solo lectura)
- ✅ Crea usuarios reales en Teams (reversible)
- ✅ **NO envía emails** (MailHog los captura)
- ⚠️ Maneja con cuidado datos de estudiantes

### En PRODUCCIÓN:
- ⚠️ Envía emails REALES
- ⚠️ Crea usuarios permanentes
- ⚠️ Requiere monitoreo y backups
- 🔒 SSL/HTTPS obligatorio

---

## 📋 Checklist de Verificación

### Antes de TESTING REAL:
- [ ] Obtener credenciales reales de API UTI
- [ ] Obtener token real de Moodle
- [ ] Verificar credenciales de Teams
- [ ] Configurar .env.testing.real
- [ ] Hacer backup de base de datos
- [ ] Verificar que MailHog esté corriendo

### Antes de PRODUCCIÓN:
- [ ] Testing real completado exitosamente
- [ ] Configurar SMTP real
- [ ] Configurar SSL/HTTPS
- [ ] Configurar backups automáticos
- [ ] Configurar monitoreo
- [ ] Plan de rollback
- [ ] Documentar procedimientos
