# Deployment Rápido - PyLucy Testing

## En el Servidor de Testing

### 1. Clonar el repositorio (HTTPS - sin SSH)

```bash
# Conectarse al servidor
ssh usuario@servidor-testing.unrc.edu.ar

# Ir al directorio donde quieras instalar
cd /opt  # o /home/usuario o donde prefieras

# Clonar con HTTPS
git clone https://github.com/TU-USUARIO/pylucy.git
cd pylucy
```

### 2. Setup inicial

```bash
# Crear archivo de configuración
./deploy.sh setup
```

### 3. Editar configuración

```bash
# Editar .env.prod
nano .env.prod
```

**Variables MÍNIMAS que DEBES cambiar:**

```bash
# Django
ALLOWED_HOSTS=servidor-testing.unrc.edu.ar,IP_DEL_SERVIDOR

# Base de datos
DB_PASSWORD=CAMBIAR_ESTO_POR_CONTRASEÑA_SEGURA

# SIAL (si no tienes credenciales, déjalas como están para usar mock)
SIAL_BASE_URL=http://mock-api:8088  # o la URL real
SIAL_BASIC_USER=tu_usuario
SIAL_BASIC_PASS=tu_contraseña

# Las demás puedes dejarlas como están para testing inicial
```

### 4. Iniciar todo

```bash
# Iniciar servicios
./deploy.sh start

# Esperar 30 segundos y verificar
./deploy.sh status
```

### 5. Crear superusuario

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 6. Acceder

- Aplicación: `http://IP_SERVIDOR` o `http://nombre-servidor`
- Admin: `http://IP_SERVIDOR/admin`

## Comandos Útiles

```bash
# Ver logs en tiempo real
./deploy.sh logs

# Ver solo logs de Django
docker compose -f docker-compose.prod.yml logs -f web

# Reiniciar todo
./deploy.sh restart

# Detener todo
./deploy.sh stop

# Backup de base de datos
./deploy.sh backup

# Actualizar código (después de git pull)
./deploy.sh update
```

## Actualizar cuando hagas cambios

```bash
cd /opt/pylucy
git pull
./deploy.sh update
```

## ⚠️ MIGRACIÓN ESPECIAL: Configuración Inicial (Solo Primera Vez)

**IMPORTANTE**: La migración `0016_populate_configuracion` carga la configuración inicial del sistema con credenciales reales. **Solo se ejecuta UNA VEZ**.

### Aplicar en Testing

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py migrate alumnos 0016
```

### Aplicar en Producción

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate alumnos 0016
```

**¿Qué configura esta migración?**
- Credenciales Azure/Teams (tenant, client_id, client_secret)
- Credenciales Moodle (URL: v.eco.unrc.edu.ar, token, auth method: oauth2)
- API SIAL/UTI (URL, usuario, contraseña)
- Plantillas HTML de emails (bienvenida, credenciales, password)
- Configuración SMTP (MailHog para testing)
- Rate limits y batch size

**Verificar que se aplicó correctamente:**

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "from alumnos.models import Configuracion; c = Configuracion.load(); print(f'Teams Tenant: {c.teams_tenant_id}'); print(f'Moodle URL: {c.moodle_base_url}'); print(f'Moodle Token: {c.moodle_wstoken[:20]}...')"
```

**Si necesitas exportar/modificar la configuración:**

```bash
# Exportar a JSON
docker compose -f docker-compose.testing.yml exec web python manage.py config export --file /app/config.json
docker cp pylucy-web-testing:/app/config.json ./configuracion.json

# Editar configuracion.json manualmente

# Importar desde JSON
docker cp ./configuracion.json pylucy-web-testing:/app/config.json
docker compose -f docker-compose.testing.yml exec web python manage.py config import --file /app/config.json
```

## Si algo falla

```bash
# Ver qué pasó
./deploy.sh logs

# Ver estado
./deploy.sh status

# Reiniciar todo
./deploy.sh restart

# Si todo está mal, empezar de cero (¡CUIDADO! Borra datos)
./deploy.sh clean
./deploy.sh start
```

## Estructura de Servicios

- **nginx** (puerto 80): Servidor web
- **web**: Django con Gunicorn
- **db**: PostgreSQL
- **redis**: Cache y broker de Celery
- **celery**: Worker para tareas asíncronas
- **celery-beat**: Scheduler de tareas periódicas

Todo está en contenedores Docker, no necesitas instalar nada más.

## Verificar que funciona

```bash
# Todos los servicios deben estar "Up" y "healthy"
./deploy.sh status

# Debe responder con HTML
curl http://localhost/admin/login/

# Desde tu navegador
http://IP_SERVIDOR
```

## Problemas Comunes

### Error: "Cannot connect to database"
- Verificar que DB_PASSWORD esté configurada en .env.prod
- Reiniciar: `./deploy.sh restart`

### Error: "502 Bad Gateway"
- Ver logs: `docker compose -f docker-compose.prod.yml logs web`
- Verificar migraciones: `docker compose -f docker-compose.prod.yml exec web python manage.py migrate`

### Archivos estáticos no cargan
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
./deploy.sh restart
```

## Documentación Completa

Ver `docs/DEPLOYMENT.md` para información detallada.
