# PyLucy - Sistema de Gestión de Alumnos

Sistema automatizado de gestión de alumnos para la Facultad de Ciencias Económicas (UNRC).

## 🚀 Quick Start

### Actualizar código y reiniciar servicios

```bash
./update-testing-prod.sh testing   # Para testing
./update-testing-prod.sh prod      # Para producción
```

### Comandos comunes

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

## 📚 Documentación

- **[DEPLOY-QUICK.md](DEPLOY-QUICK.md)** - Guía rápida de deployment
- **[docs/CONFIGURACION.md](docs/CONFIGURACION.md)** - 📋 **Configuración JSON (export/import)**
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Documentación completa de deployment

## 🎯 Configuración con JSON

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

## 🔧 Archivo de configuración

El archivo `configuracion_real.json` contiene todas las credenciales y settings del sistema:

- **Teams/Azure AD**: tenant_id, client_id, client_secret
- **SIAL/UTI**: URL, usuario, contraseña
- **Moodle**: URL, token, método de auth (manual/oauth2/oidc)
- **Email**: Plantillas HTML, SMTP settings
- **Rate Limits**: Límites de procesamiento

Ver [docs/CONFIGURACION.md](docs/CONFIGURACION.md) para detalles completos.

## 🛠️ Servicios

- **web**: Django + Gunicorn
- **db**: PostgreSQL
- **redis**: Cache y broker de Celery
- **celery**: Worker para tareas asíncronas
- **celery-beat**: Scheduler de tareas periódicas
- **nginx**: Servidor web (solo producción)
- **mailhog**: SMTP testing (solo testing)

## 📊 Admin

Accede al admin en: `http://IP_SERVIDOR/admin`

### Acciones disponibles:

**Teams:**
- 🚀 Activar Teams + Enviar Email con credenciales
- 🔄 Generar contraseña y enviar correo
- 👤 Crear usuario en Teams (sin email)
- 🔑 Resetear contraseña Teams

**Moodle:**
- 🎓 Enrollar en Moodle (con email de bienvenida)
- 🎓 Enrollar en Moodle (sin email)

**General:**
- 📧 Enviar email de bienvenida masivo

**Borrado:**
- 🗑️ Borrar solo de Teams
- 🗑️ Borrar solo de Moodle

## 🔐 Métodos de Autenticación Moodle

- `manual` - Autenticación manual (usuario/contraseña)
- `oauth2` - OAuth2 (Microsoft Teams)
- `oidc` - OpenID Connect (recomendado, default)

## 📝 Ver Logs

```bash
# Logs de la aplicación
./comandos-comunes.sh logs testing

# Logs de Celery
./comandos-comunes.sh logs-celery testing

# Logs del admin Django
http://IP_SERVIDOR/admin/alumnos/log/
```

## 🆘 Troubleshooting

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

## 🏗️ Estructura del Proyecto

```
pylucy/
├── src/
│   ├── alumnos/          # App principal
│   │   ├── models.py     # Modelos (Alumno, Configuracion, Log, Tarea)
│   │   ├── admin.py      # Admin de Django
│   │   ├── tasks.py      # Tareas de Celery
│   │   ├── services/     # Servicios (Teams, Moodle, Email, SIAL)
│   │   └── management/   # Comandos custom (config export/import)
│   ├── cursos/           # App de cursos
│   └── pylucy/           # Configuración del proyecto
├── docs/                 # Documentación
├── configuracion_real.json  # Configuración con credenciales reales
├── update-testing-prod.sh   # Script de actualización
├── comandos-comunes.sh      # Scripts útiles
└── docker-compose.*.yml     # Configuración Docker
```

## 📞 Soporte

Para problemas o dudas, consulta la documentación completa en `docs/`.
