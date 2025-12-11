# Servicios Docker y Acceso - PyLucy Testing

## 📦 Servicios del Docker Compose

El archivo `docker-compose.testing.yml` levanta **8 servicios** en contenedores Docker:

### 1️⃣ **db** - Base de Datos PostgreSQL
- **Imagen**: `postgres:16`
- **Puerto**: `5432:5432` (expuesto)
- **Propósito**: Base de datos principal de PyLucy
- **Credenciales**:
  - Usuario: `pylucy`
  - Contraseña: `pylucy`
  - Base de datos: `pylucy`
- **Volumen**: `pylucy-db-testing` (datos persistentes)
- **Healthcheck**: Verifica que PostgreSQL esté listo cada 10 segundos

**Conectarse desde fuera del contenedor**:
```bash
psql -h localhost -p 5432 -U pylucy -d pylucy
# Password: pylucy
```

---

### 2️⃣ **redis** - Cache y Message Broker
- **Imagen**: `redis:7-alpine`
- **Puerto**: `6379:6379` (expuesto)
- **Propósito**:
  - Cache de Django
  - Broker de mensajes para Celery (tareas asíncronas)
  - Backend de resultados de Celery
- **Persistencia**: Modo `appendonly` (guarda datos en disco)
- **Volumen**: `pylucy-redis-testing`
- **Healthcheck**: Ping a Redis cada 10 segundos

**Conectarse**:
```bash
redis-cli -h localhost -p 6379
# > PING
# PONG
```

---

### 3️⃣ **web** - Aplicación Django
- **Build**: Construida desde `Dockerfile` local
- **Puerto**: `8000:8000` (expuesto)
- **Comando**: `python manage.py runserver 0.0.0.0:8000`
- **Propósito**: Servidor web de la aplicación PyLucy
- **Variables de entorno**: Cargadas desde `.env.dev`
- **Volúmenes**:
  - `./src:/app` (código fuente montado en tiempo real)
  - `pylucy-static-testing:/app/staticfiles` (archivos estáticos)
- **Depende de**: db (healthy) y redis (healthy)
- **Reinicio**: Automático siempre

**Acceder**:
- Aplicación: `http://IP_SERVIDOR:8000/`
- Admin: `http://IP_SERVIDOR:8000/admin/`

---

### 4️⃣ **celery** - Worker de Tareas Asíncronas
- **Build**: Misma imagen que `web`
- **Comando**: `celery -A pylucy worker -l info`
- **Propósito**: Procesa tareas en segundo plano:
  - Sincronización con SIAL/UTI
  - Sincronización con Moodle
  - Creación de usuarios en Teams
  - Envío de emails
- **Concurrencia**: Predeterminada (multi-proceso)
- **Logs**: Nivel INFO
- **Volumen**: `./src:/app` (mismo código que web)

**Ver tareas activas**:
```bash
docker compose -f docker-compose.testing.yml exec celery celery -A pylucy inspect active
```

---

### 5️⃣ **celery-beat** - Scheduler de Tareas Periódicas
- **Build**: Misma imagen que `web`
- **Comando**: `celery -A pylucy beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`
- **Propósito**: Programa tareas periódicas:
  - Ingesta automática de preinscriptos desde SIAL
  - Sincronizaciones programadas
  - Tareas de mantenimiento
- **Scheduler**: Basado en base de datos (configuración desde Django Admin)
- **Volumen**: `./src:/app`

**Tareas periódicas** se configuran en:
- Django Admin → Periodic Tasks

---

### 6️⃣ **mailhog** - Captura de Emails
- **Imagen**: `mailhog/mailhog`
- **Puertos**:
  - `8025:8025` (UI Web)
  - `1025:1025` (Servidor SMTP)
- **Propósito**:
  - Captura todos los emails enviados por PyLucy
  - NO envía emails reales (ideal para testing)
  - Interfaz web para ver los emails
- **Sin persistencia**: Los emails se pierden al reiniciar

**Acceder**:
- UI Web: `http://IP_SERVIDOR:8025/`
- Configuración SMTP en `.env.dev`:
  ```
  EMAIL_HOST=mailhog
  EMAIL_PORT=1025
  EMAIL_USE_TLS=False
  ```

---

### 7️⃣ **mock-api-uti** - API Mock de SIAL/UTI
- **Build**: Construida desde `./mock-api-uti`
- **Puerto**: `8088:8000` (expuesto)
- **Propósito**:
  - Simula la API de SIAL/UTI para testing
  - Devuelve datos de prueba para preinscriptos
  - Evita depender de servicios externos en testing
- **Credenciales**:
  - Usuario: `usuario`
  - Contraseña: `contrasena`
  - Autenticación: HTTP Basic Auth
- **Endpoints disponibles**:
  - `/webservice/sial/V2/04/preinscriptos/listas/{desde}/{hasta}`
  - `/webservice/sial/V2/04/preinscriptos/preinscripto/{nro_tramite}`

**Configuración en `.env.dev`**:
```bash
SIAL_BASE_URL=http://mock-api-uti:8000
SIAL_BASIC_USER=usuario
SIAL_BASIC_PASS=contrasena
```

**Importante**: En el servidor de testing, el servicio web se conecta al mock usando el nombre del contenedor `mock-api-uti` a través de la red `pylucy-net`. NO usa `host.docker.internal` (que no funciona en Linux).

---

### 8️⃣ **pgadmin** - Administrador de PostgreSQL
- **Imagen**: `dpage/pgadmin4`
- **Puerto**: `5050:80` (expuesto)
- **Propósito**: Interfaz web para administrar la base de datos
- **Credenciales de acceso**:
  - Email: `admin@unrc.edu.ar`
  - Password: `admin`

**Acceder**:
1. Ir a: `http://IP_SERVIDOR:5050/`
2. Login: `admin@unrc.edu.ar` / `admin`
3. Add Server:
   - Name: PyLucy
   - Connection:
     - Host: `db`
     - Port: `5432`
     - Database: `pylucy`
     - Username: `pylucy`
     - Password: `pylucy`

---

## 🌐 Red y Volúmenes

### Red
- **Nombre**: `pylucy-net`
- **Driver**: bridge
- **Propósito**: Conecta todos los servicios entre sí

Los contenedores pueden comunicarse usando sus nombres:
- `web` se conecta a `db:5432`
- `celery` se conecta a `redis:6379`

### Volúmenes Persistentes
1. **pylucy-db-testing**: Datos de PostgreSQL
2. **pylucy-redis-testing**: Datos de Redis
3. **pylucy-static-testing**: Archivos estáticos de Django

---

## 👤 Usuarios y Credenciales

### Usuario por Defecto (Automático)

Al iniciar el contenedor `web`, se crea automáticamente:

- **Usuario**: `admin`
- **Contraseña**: `admin`
- **Email**: `admin@unrc.edu.ar`
- **Permisos**: Superuser (acceso total)

### Crear Usuario Personalizado: AdminFCE.16

Para crear el usuario `AdminFCE.16` con password `Milei2027!`, ejecuta:

```bash
# En el servidor
cd /home/motorola/pylucy

# Opción 1: Usar Django shell
docker compose -f docker-compose.testing.yml exec web python manage.py shell
```

Luego pega este código:

```python
from django.contrib.auth.models import User

# Crear el usuario
user = User.objects.create_user(
    username='AdminFCE.16',
    email='adminfce@eco.unrc.edu.ar',
    password='Milei2027!',
    first_name='Admin',
    last_name='FCE'
)

# Darle permisos de superuser
user.is_superuser = True
user.is_staff = True
user.save()

print(f'✅ Usuario creado: {user.username}')
print(f'   Email: {user.email}')
print(f'   Superuser: {user.is_superuser}')
print(f'   Staff: {user.is_staff}')
```

**O usando un one-liner**:

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.create_superuser('AdminFCE.16', 'adminfce@eco.unrc.edu.ar', 'Milei2027!')
print('✅ Usuario AdminFCE.16 creado con éxito')
"
```

### Verificar que el usuario fue creado:

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django.contrib.auth.models import User
users = User.objects.filter(username='AdminFCE.16')
if users.exists():
    u = users.first()
    print(f'Usuario: {u.username}')
    print(f'Email: {u.email}')
    print(f'Superuser: {u.is_superuser}')
    print(f'Staff: {u.is_staff}')
else:
    print('Usuario no encontrado')
"
```

### Resetear contraseña de un usuario existente:

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='AdminFCE.16')
user.set_password('Milei2027!')
user.save()
print('✅ Contraseña actualizada')
"
```

---

## 🔐 Resumen de Credenciales

| Servicio | URL | Usuario | Contraseña |
|----------|-----|---------|------------|
| **PyLucy Admin** | http://IP:8000/admin/ | `admin` | `admin` |
| **PyLucy Admin** | http://IP:8000/admin/ | `AdminFCE.16` | `Milei2027!` |
| **MailHog** | http://IP:8025/ | - | - |
| **PgAdmin** | http://IP:5050/ | `admin@unrc.edu.ar` | `admin` |
| **PostgreSQL** | localhost:5432 | `pylucy` | `pylucy` |
| **Redis** | localhost:6379 | - | - |

---

## 📊 Comandos Útiles

### Ver estado de todos los servicios:
```bash
docker compose -f docker-compose.testing.yml ps
```

### Ver logs en tiempo real:
```bash
# Todos los servicios
docker compose -f docker-compose.testing.yml logs -f

# Solo web
docker compose -f docker-compose.testing.yml logs -f web

# Solo celery
docker compose -f docker-compose.testing.yml logs -f celery
```

### Reiniciar un servicio específico:
```bash
docker compose -f docker-compose.testing.yml restart web
```

### Ejecutar comandos Django:
```bash
# Migraciones
docker compose -f docker-compose.testing.yml exec web python manage.py migrate

# Crear superuser interactivo
docker compose -f docker-compose.testing.yml exec web python manage.py createsuperuser

# Shell de Django
docker compose -f docker-compose.testing.yml exec web python manage.py shell

# Colectar archivos estáticos
docker compose -f docker-compose.testing.yml exec web python manage.py collectstatic --noinput
```

### Acceder a la shell de un contenedor:
```bash
docker compose -f docker-compose.testing.yml exec web bash
```

---

## 🚀 Orden de Inicio

Los servicios inician en este orden (por dependencias):

1. **db** (PostgreSQL) - Se espera healthcheck
2. **redis** - Se espera healthcheck
3. **web** (Django) - Depende de db y redis
4. **celery** - Depende de db y redis
5. **celery-beat** - Depende de db y redis
6. **mailhog** - Independiente
7. **pgadmin** - Independiente

El **entrypoint** del contenedor `web` ejecuta automáticamente:
1. Espera a que la DB esté lista
2. Ejecuta migraciones
3. Colecta archivos estáticos
4. Crea superuser `admin/admin` si no existe
5. Inicia el servidor Django

---

## 🛠️ Troubleshooting

### Un servicio no inicia:
```bash
docker compose -f docker-compose.testing.yml logs nombre_servicio
```

### Resetear todo (¡CUIDADO! Borra datos):
```bash
docker compose -f docker-compose.testing.yml down -v
docker compose -f docker-compose.testing.yml up -d
```

### Ver recursos usados:
```bash
docker stats
```

### Limpiar espacio:
```bash
docker system prune -a
```
