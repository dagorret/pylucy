# **Entorno de Desarrollo de pyLucy**

## 🧱 Objetivo del documento

Este documento explica **cómo funciona el entorno de desarrollo de pyLucy usando Docker**, qué servicios intervienen y cómo ejecutar cualquier comando de Django dentro del contenedor.

Este archivo complementa `00-architecture.md` y define el flujo de trabajo recomendado en modo:

> **Siempre Docker**

---

# 🚀 1. Servicios del entorno de desarrollo (`docker-compose.dev.yml`)

El entorno levanta automáticamente:

| Servicio    | Contenedor           | Función                                |
| ----------- | -------------------- | -------------------------------------- |
| **web**     | `pylucy-web-dev`     | Django (con `runserver`)               |
| **db**      | `pylucy-db-dev`      | PostgreSQL 16                          |
| **pgadmin** | `pylucy-pgadmin-dev` | Interfaz web para administrar Postgres |

Todos viven en la red interna de Docker:

`pylucy-net`

---

# 🧩 2. Estructura de desarrollo

`pylucy/ ├── src/                → Código Django │   ├── manage.py │   └── pylucy/ │       ├── settings.py │       ├── urls.py │       └── ... ├── docker-compose.dev.yml ├── Dockerfile ├── dj                  → Helper para ejecutar manage.py dentro de Docker ├── dev.sh              → Inicia el entorno de desarrollo └── requirements.txt`

---

# 🐳 3. Cómo iniciar el entorno de desarrollo

Simplemente ejecutar:

`./dev.sh`

Esto inicia:

- Django en el contenedor `pylucy-web-dev`

- Postgres en `pylucy-db-dev`

- pgAdmin en `pylucy-pgadmin-dev`

Accesos:

- Django → http://localhost:8000

pgAdmin → http://localhost:5050

---

# 🧠 4. Código en tu máquina, ejecución en Docker

El código se encuentra **en tu máquina**, dentro del directorio:

`src/`

y Docker lo monta en:

`/app/`

por lo cual:

- Editas tu código localmente.

- Django dentro del contenedor detecta los cambios.

- No necesitás reconstruir la imagen mientras desarrollas.

---

# ⚙️ 5. Ejecutar comandos de Django dentro del contenedor

Como Django corre **dentro de Docker**, todos los comandos se ejecutan allí.

Para simplificar el uso creamos el script `./dj`:

`./dj <comando>`

Ejemplos:

### 🔧 Migraciones

`./dj makemigrations ./dj migrate`

### 👤 Crear superusuario

`./dj createsuperuser`

### 🧪 Ejecutar tests

`./dj test`

### 🐚 Entrar a la shell de Django

`./dj shell`

---

# 🗄️ 6. Base de datos en desarrollo

El entorno usa **PostgreSQL 16**, en el contenedor:

`pylucy-db-dev`

Django se conecta automáticamente gracias a estas variables del `docker-compose.dev.yml`:

`- DB_ENGINE=django.db.backends.postgresql - DB_NAME=pylucy - DB_USER=pylucy - DB_PASSWORD=pylucy - DB_HOST=db - DB_PORT=5432`

---

# 🛠️ 7. pgAdmin para administrar la base

- URL: http://localhost:5050

- Usuario: `admin@local.test`

- Password: `admin`

Añadir un servidor con estos datos:

- Host: `db`

- User: `pylucy`

- Pass: `pylucy`

- Base: `pylucy`

---

# 🧪 8. Cambios en requerimientos

Cada vez que agregues un paquete a `requirements.txt`:

`docker compose -f docker-compose.dev.yml build web ./dev.sh`

---

# 📦 9. Entorno local sin Docker (opcional)

Si alguna vez querés correr Django en modo venv local, `settings.py` ya está preparado:

- Usa **SQLite** si *NO existen* variables `DB_ENGINE`.

- Usa **Postgres (Docker)** si *sí existen*.

Pero el flujo recomendado es siempre Docker.

---

# 🏁 10. Conclusión

Con este entorno:

- Django corre aislado dentro del contenedor `web`.

- Postgres corre en `db`.

- Editás código localmente.

- Django detecta cambios al instante (hot reload).

- Todos los comandos se ejecutan con `./dj`.

Todo esto hace el desarrollo **simple, reproducible y coherente** con la arquitectura final de pyLucy.

---

Si querés, puedo generar también `doc/02-modelado-alumnos.md` con:

- Diagrama de tablas

- Modelos Django sugeridos

- Relaciones FK

- Flujo entre aspirantes/ingresantes/alumnos.
