# Guía de Deployment - PyLucy (Producción)

## Requisitos del Servidor

- **Sistema Operativo**: Ubuntu 20.04+ o Debian 11+
- **Docker**: Versión 20.10+
- **Docker Compose**: Versión 2.0+
- **RAM**: Mínimo 4GB (Recomendado 8GB)
- **CPU**: Mínimo 2 cores (Recomendado 4 cores)
- **Disco**: Mínimo 20GB libres
- **Puertos abiertos**:
  - 80 (HTTP)
  - 443 (HTTPS, opcional para futuro)

---

## Paso 1: Preparar el Servidor

### 1.1. Instalar Docker

```bash
# Actualizar sistema
sudo apt-get update
sudo apt-get upgrade -y

# Instalar dependencias
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Agregar repositorio de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verificar instalación
docker --version
docker compose version
```

### 1.2. Configurar usuario para Docker (opcional pero recomendado)

```bash
# Agregar tu usuario al grupo docker
sudo usermod -aG docker $USER

# Aplicar cambios (cerrar sesión y volver a entrar)
newgrp docker

# Verificar que puedes ejecutar docker sin sudo
docker ps
```

---

## Paso 2: Transferir Código al Servidor

### Opción A: Desde Git (Recomendado)

```bash
# En el servidor
cd /home/tu-usuario
git clone https://github.com/tu-org/pylucy.git
cd pylucy
```

### Opción B: Transferencia Manual (SCP)

```bash
# Desde tu máquina local
# Crear tarball excluyendo archivos innecesarios
tar --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env*' \
    --exclude='src/static' \
    -czf pylucy.tar.gz /home/carlos/work/pylucy

# Transferir al servidor
scp pylucy.tar.gz usuario@servidor.unrc.edu.ar:/home/usuario/

# En el servidor
ssh usuario@servidor.unrc.edu.ar
cd /home/usuario
tar -xzf pylucy.tar.gz
cd pylucy
```

---

## Paso 3: Configurar Variables de Entorno

### 3.1. Copiar plantilla

```bash
cp .env.prod.example .env.prod
```

### 3.2. Editar configuración

```bash
nano .env.prod
```

### 3.3. Variables CRÍTICAS a configurar

**Seguridad:**
```bash
# Generar SECRET_KEY segura
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

# Editar .env.prod y pegar el SECRET_KEY generado
```

**Base de Datos:**
```bash
DB_PASSWORD=contraseña_segura_postgresql
```

**Dominio:**
```bash
ALLOWED_HOSTS=servidor.unrc.edu.ar,eco.unrc.edu.ar
```

**Email SMTP:**
```bash
EMAIL_HOST=smtp.eco.unrc.edu.ar
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=no-reply@eco.unrc.edu.ar
EMAIL_HOST_PASSWORD=contraseña_smtp
```

**Teams/Azure AD:**
```bash
TEAMS_TENANT=GUID_del_tenant
TEAMS_CLIENT_ID=GUID_del_client_id
TEAMS_CLIENT_SECRET=secreto_del_client
```

**Moodle:**
```bash
MOODLE_BASE_URL=https://moodle.eco.unrc.edu.ar
MOODLE_WSTOKEN=token_de_webservices
```

**SIAL:**
```bash
SIAL_BASE_URL=https://sial.unrc.edu.ar
SIAL_BASIC_USER=usuario_api
SIAL_BASIC_PASS=contraseña_api
```

**Modo:**
```bash
ENVIRONMENT_MODE=production  # o 'testing' para fase alfa
ACCOUNT_PREFIX=a             # o 'test-a' para testing
```

---

## Paso 4: Iniciar Servicios

### 4.1. Ejecutar script de deployment

```bash
chmod +x prod.sh
./prod.sh
```

El script automáticamente:
1. Verifica que Docker esté corriendo
2. Detiene servicios previos si existen
3. Construye las imágenes
4. Ejecuta migraciones de base de datos
5. Recolecta archivos estáticos
6. Levanta todos los servicios:
   - PostgreSQL
   - Redis
   - Django (Gunicorn)
   - Celery Worker
   - Celery Beat
   - Nginx

### 4.2. Verificar servicios

```bash
# Ver estado
docker compose -f docker-compose.prod.yml ps

# Ver logs
docker compose -f docker-compose.prod.yml logs -f
```

**Servicios esperados:**
```
NAME                     STATUS
pylucy-db-prod          healthy
pylucy-redis-prod       healthy
pylucy-web-prod         healthy
pylucy-celery-prod      healthy
pylucy-celery-beat-prod running
pylucy-nginx-prod       healthy
```

---

## Paso 5: Configuración Inicial

### 5.1. Crear superusuario

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Ingresar:
- Username: admin
- Email: admin@eco.unrc.edu.ar
- Password: (elegir contraseña segura)

### 5.2. Configurar tareas periódicas

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py setup_periodic_tasks
```

### 5.3. Acceder al Admin

```
http://servidor.unrc.edu.ar/admin
```

Iniciar sesión con el superusuario creado.

### 5.4. Configurar sistema desde el Admin

**Ir a: Alumnos > Configuración del Sistema**

Configurar:
- **Procesamiento en Lotes**: `batch_size=20`, `rate_limit_teams=10`, `rate_limit_moodle=30`
- **Ingesta de Preinscriptos**: Configurar fechas y frecuencia según calendario académico
- **Ingesta de Aspirantes**: Configurar fechas y frecuencia
- **Ingesta de Ingresantes**: Configurar fechas y frecuencia

**Credenciales (opcional):**
- Si las credenciales en `.env.prod` están correctas, dejar vacío
- Si necesitas sobrescribir temporalmente, llenar en el Admin

---

## Paso 6: Testing en Producción (Fase Alfa)

### 6.1. Verificar conectividad

```bash
# Desde el servidor
curl -I http://localhost/admin/login/

# Debería retornar: HTTP/1.1 200 OK
```

### 6.2. Test de servicios externos

**Test SIAL:**
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py shell
```

```python
from alumnos.services.ingesta import SIALClient

client = SIALClient()
listas = client.fetch_listas('preinscriptos', n=5)
print(f"Registros obtenidos: {len(listas)}")
```

**Test Teams:**
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py shell
```

```python
from alumnos.services.teams_service import TeamsService

ts = TeamsService()
print(f"Tenant: {ts.tenant}")
print(f"Configuración OK" if ts.tenant else "ERROR: Configuración incompleta")
```

### 6.3. Ingesta manual de prueba

```bash
# Ingestar 5 preinscriptos de prueba
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "
from alumnos.services.ingesta import ingerir_desde_sial
created, updated, errors = ingerir_desde_sial('preinscriptos', n=5)
print(f'Creados: {created}, Actualizados: {updated}, Errores: {len(errors)}')
"
```

### 6.4. Monitoreo de logs

```bash
# Logs en tiempo real
docker compose -f docker-compose.prod.yml logs -f

# Logs de Celery (tareas en background)
docker compose -f docker-compose.prod.yml logs -f celery

# Logs de Nginx (requests HTTP)
docker compose -f docker-compose.prod.yml logs -f nginx
```

---

## Mantenimiento

### Ver logs

```bash
# Todos los servicios
docker compose -f docker-compose.prod.yml logs -f

# Servicio específico
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f celery
docker compose -f docker-compose.prod.yml logs -f celery-beat
```

### Reiniciar servicios

```bash
# Reiniciar todos
docker compose -f docker-compose.prod.yml restart

# Reiniciar servicio específico
docker compose -f docker-compose.prod.yml restart web
docker compose -f docker-compose.prod.yml restart celery
```

### Detener servicios

```bash
docker compose -f docker-compose.prod.yml down
```

### Actualizar código (deploy de nueva versión)

```bash
# Desde Git
git pull origin main

# O transferir nuevo tarball y extraer

# Rebuild y restart
docker compose -f docker-compose.prod.yml down
./prod.sh
```

### Backup de base de datos

```bash
# Crear backup
docker compose -f docker-compose.prod.yml exec db pg_dump -U pylucy pylucy > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
cat backup_YYYYMMDD_HHMMSS.sql | docker compose -f docker-compose.prod.yml exec -T db psql -U pylucy pylucy
```

### Ver estado de tareas Celery

```bash
docker compose -f docker-compose.prod.yml exec celery celery -A pylucy inspect active
docker compose -f docker-compose.prod.yml exec celery celery -A pylucy inspect scheduled
```

---

## Troubleshooting

### Error: "Can't connect to database"

**Verificar:**
```bash
# Estado de PostgreSQL
docker compose -f docker-compose.prod.yml exec db pg_isready -U pylucy

# Logs de DB
docker compose -f docker-compose.prod.yml logs db
```

**Solución:**
- Verificar `DB_PASSWORD` en `.env.prod`
- Reiniciar servicios: `docker compose -f docker-compose.prod.yml restart db web`

---

### Error: "502 Bad Gateway" en Nginx

**Causa:** Django/Gunicorn no está respondiendo

**Verificar:**
```bash
# Estado de web
docker compose -f docker-compose.prod.yml ps web

# Logs de web
docker compose -f docker-compose.prod.yml logs web
```

**Solución:**
```bash
docker compose -f docker-compose.prod.yml restart web
```

---

### Celery workers no procesan tareas

**Verificar:**
```bash
# Ping a workers
docker compose -f docker-compose.prod.yml exec celery celery -A pylucy inspect ping

# Logs de celery
docker compose -f docker-compose.prod.yml logs celery
```

**Solución:**
```bash
docker compose -f docker-compose.prod.yml restart celery celery-beat
```

---

### Tareas periódicas no se ejecutan

**Verificar:**
```bash
# Logs de celery-beat
docker compose -f docker-compose.prod.yml logs celery-beat

# Verificar configuración en admin
# http://servidor/admin/alumnos/configuracion/
```

**Solución:**
1. Verificar que `preinscriptos_dia_inicio` esté configurado
2. Verificar que `preinscriptos_frecuencia_segundos` esté configurado
3. Reiniciar beat: `docker compose -f docker-compose.prod.yml restart celery-beat`

---

### Usuarios Teams no se crean

**Verificar credenciales:**
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py shell
```

```python
from alumnos.services.teams_service import TeamsService
from alumnos.models import Configuracion

config = Configuracion.load()
print(f"Tenant DB: {config.teams_tenant_id or '(vacío -> usa ENV)'}")

ts = TeamsService()
token = ts._get_token()
print(f"Token obtenido: {'OK' if token else 'ERROR'}")
```

**Solución:**
- Verificar `TEAMS_TENANT`, `TEAMS_CLIENT_ID`, `TEAMS_CLIENT_SECRET` en `.env.prod`
- O llenarlos en Admin: http://servidor/admin/alumnos/configuracion/

---

## Configuración de Firewall (Opcional)

```bash
# Permitir HTTP y HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Permitir SSH
sudo ufw allow 22/tcp

# Activar firewall
sudo ufw enable

# Ver estado
sudo ufw status
```

---

## SSL/HTTPS (Futuro)

Para habilitar HTTPS con Let's Encrypt:

1. Instalar Certbot
2. Generar certificados
3. Actualizar `deploy/nginx/nginx.conf`
4. Descomentar puerto 443 en `docker-compose.prod.yml`

**Documentación detallada:** (Por agregar en futuro deployment)

---

## Comandos Rápidos de Referencia

```bash
# Iniciar servicios
./prod.sh

# Ver logs en tiempo real
docker compose -f docker-compose.prod.yml logs -f

# Reiniciar todo
docker compose -f docker-compose.prod.yml restart

# Detener todo
docker compose -f docker-compose.prod.yml down

# Crear superusuario
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Shell de Django
docker compose -f docker-compose.prod.yml exec web python manage.py shell

# Ejecutar comando Django
docker compose -f docker-compose.prod.yml exec web python manage.py <comando>

# Backup DB
docker compose -f docker-compose.prod.yml exec db pg_dump -U pylucy pylucy > backup.sql

# Ver estado de Celery
docker compose -f docker-compose.prod.yml exec celery celery -A pylucy inspect active
```

---

**Última actualización**: 2025-12-11
**Versión**: 1.0 (Fase Alfa)
