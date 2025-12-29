# Lucy AMS - Academic Management System

Sistema de Gestión Académica para la Facultad de Ciencias Económicas de la Universidad Nacional de Río Cuarto (UNRC).

**Versión:** 0.98
**Autor:** Carlos Dagorret
**Licencia:** MIT

---

## Acerca del Sistema

Lucy AMS es un sistema de gestión académica que integra múltiples servicios externos (Microsoft Teams, Moodle, UTI/SIAL) para automatizar procesos administrativos relacionados con la gestión de estudiantes.

**Para información detallada sobre el sistema, conceptos técnicos, arquitectura y referencias, consulte:**

**[SOBRE_LUCY.md](SOBRE_LUCY.md)** - Documentación completa del sistema

---

## Inicio Rápido

### Requisitos Previos

- Docker y Docker Compose
- Python 3.12+ (para desarrollo local)
- PostgreSQL 16
- Redis 7

### Instalación

1. **Clonar el repositorio**

```bash
git clone https://github.com/tu-usuario/lucy.git
cd lucy
```

2. **Configurar variables de entorno**

```bash
cp .env.example .env.dev
nano .env.dev
```

3. **Configurar credenciales de servicios**

```bash
cd credenciales/
cp uti_credentials.json.example uti_credentials.json
cp moodle_credentials.json.example moodle_credentials.json
cp teams_credentials.json.example teams_credentials.json
# Edita cada archivo con tus credenciales reales
```

Ver documentación completa: [CONFIGURACION.md](CONFIGURACION.md)

4. **Iniciar el sistema**

```bash
./deploy-testing.sh start
```

5. **Acceder**

- Aplicación: http://localhost:8000
- Admin: http://localhost:8000/admin
- MailHog (testing): http://localhost:8025

---

## Actualizar código y reiniciar servicios

```bash
./update-testing-prod.sh testing   # Para testing
./update-testing-prod.sh prod      # Para producción
```

---

## Comandos Comunes

```bash
# Ver logs en tiempo real
./comandos-comunes.sh logs testing

# Ver estado de servicios
./comandos-comunes.sh status testing

# Abrir Django shell
./comandos-comunes.sh shell testing

# Hacer backup de BD
./comandos-comunes.sh backup-db testing

# Importar configuración
./comandos-comunes.sh import-config testing

# Exportar configuración
./comandos-comunes.sh export-config testing

# Verificar configuración
./comandos-comunes.sh verify-config testing
```

---

## Documentación

- **[SOBRE_LUCY.md](SOBRE_LUCY.md)** - Información completa del sistema, conceptos, arquitectura
- **[CONFIGURACION.md](CONFIGURACION.md)** - Guía completa de configuración
- **[credenciales/README.md](credenciales/README.md)** - Configuración de servicios externos
- **[DEPLOY-QUICK.md](DEPLOY-QUICK.md)** - Guía rápida de deployment
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Documentación completa de deployment

---

## Características

- **Gestión de Alumnos**: Ingesta automática desde sistema UTI/SIAL
- **Integración con Microsoft Teams**: Creación y gestión de cuentas de estudiantes
- **Integración con Moodle**: Enrollamiento automático en cursos
- **Sistema de Tareas**: Procesamiento asíncrono con Celery
- **Notificaciones por Email**: Plantillas personalizables
- **Panel de Administración**: Django Admin personalizado

---

## Configuración con JSON

### Importar configuración desde archivo

```bash
# Método 1: Con script (recomendado)
./comandos-comunes.sh import-config testing

# Método 2: Manual
docker cp configuracion_real.json pylucy-web-testing:/app/configuracion_real.json
docker compose -f docker-compose.testing.yml exec web python manage.py config import --file /app/configuracion_real.json
```

### Exportar configuración actual

```bash
# Método 1: Con script (recomendado)
./comandos-comunes.sh export-config testing
# Crea: config_export_testing_YYYYMMDD_HHMMSS.json

# Método 2: Manual
docker compose -f docker-compose.testing.yml exec web python manage.py config export --file /app/config.json
docker cp pylucy-web-testing:/app/config.json ./mi_config.json
```

### Verificar configuración

```bash
./comandos-comunes.sh verify-config testing
```

---

## Archivo de configuración

El archivo `configuracion_real.json` contiene todas las credenciales y settings del sistema:

- **Teams/Azure AD**: tenant_id, client_id, client_secret
- **SIAL/UTI**: URL, usuario, contraseña
- **Moodle**: URL, token, método de auth (manual/oauth2/oidc)
- **Email**: Plantillas HTML, SMTP settings
- **Rate Limits**: Límites de procesamiento

Ver [CONFIGURACION.md](CONFIGURACION.md) para detalles completos.

---

## Servicios

- **web**: Django + Gunicorn
- **db**: PostgreSQL 16
- **redis**: Cache y broker de Celery
- **celery**: Worker para tareas asíncronas
- **celery-beat**: Scheduler de tareas periódicas
- **nginx**: Servidor web (solo producción)
- **mailhog**: SMTP testing (solo testing)
- **pgadmin**: Administración de base de datos (solo testing)
- **mock-api-uti**: API mock para testing (solo testing)

---

## Panel de Administración

Accede al admin en: `http://IP_SERVIDOR/admin`

### Acciones disponibles:

**Teams:**
- Activar Teams + Enviar Email con credenciales
- Generar contraseña y enviar correo
- Crear usuario en Teams (sin email)
- Resetear contraseña Teams

**Moodle:**
- Enrollar en Moodle (con email de bienvenida)
- Enrollar en Moodle (sin email)

**General:**
- Enviar email de bienvenida masivo

**Borrado:**
- Borrar solo de Teams
- Borrar solo de Moodle

---

## Métodos de Autenticación Moodle

- `manual` - Autenticación manual (usuario/contraseña)
- `oauth2` - OAuth2 (Microsoft Teams)
- `oidc` - OpenID Connect (recomendado, default)

---

## Ver Logs

```bash
# Logs de la aplicación
./comandos-comunes.sh logs testing

# Logs de Celery
./comandos-comunes.sh logs-celery testing

# Logs del admin Django
http://IP_SERVIDOR/admin/alumnos/log/
```

---

## Troubleshooting

### Error: "cannot connect to database"
```bash
./comandos-comunes.sh restart testing
```

### Ver qué está pasando
```bash
./comandos-comunes.sh status testing
./comandos-comunes.sh logs testing
```

### Reiniciar todo
```bash
./update-testing-prod.sh testing
```

---

## Estructura del Proyecto

```
lucy/
├── src/
│   ├── alumnos/          # App principal
│   │   ├── models.py     # Modelos (Alumno, Configuracion, Log, Tarea)
│   │   ├── admin.py      # Admin de Django
│   │   ├── tasks.py      # Tareas de Celery
│   │   ├── services/     # Servicios (Teams, Moodle, Email, SIAL)
│   │   └── management/   # Comandos custom (config export/import)
│   ├── cursos/           # App de cursos
│   └── pylucy/           # Configuración del proyecto
├── credenciales/         # Archivos JSON con credenciales (excluidos de Git)
├── docs/                 # Documentación
├── SOBRE_LUCY.md         # Documentación completa del sistema
├── configuracion_real.json  # Configuración con credenciales reales
├── update-testing-prod.sh   # Script de actualización
├── comandos-comunes.sh      # Scripts útiles
└── docker-compose.*.yml     # Configuración Docker
```

---

## Seguridad

Este sistema maneja datos sensibles. Las credenciales se almacenan en:
- Archivos JSON en `credenciales/` (excluidos de Git)
- Variables de entorno
- Base de datos (Admin Django)

**Nunca subas credenciales a Git.**

---

## Licencia

MIT License - Copyright (c) 2025 Carlos Dagorret

---

## Soporte

Para problemas o dudas, consulta:
- [SOBRE_LUCY.md](SOBRE_LUCY.md) - Información técnica completa
- [CONFIGURACION.md](CONFIGURACION.md) - Guía de configuración
- Documentación en `docs/`

---

**Desarrollado para la FCE-UNRC**
