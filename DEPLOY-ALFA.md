# Deployment Alfa 1 - PyLucy Testing

Guía simplificada para desplegar PyLucy en el servidor de testing para pruebas alfa.
Usa configuración de desarrollo (.env.dev) con acceso a MailHog y PgAdmin.

## 🚀 Deployment Rápido

### En el Servidor de Testing

```bash
# 1. Conectarse al servidor
ssh usuario@servidor-testing.unrc.edu.ar

# 2. Clonar el repositorio con HTTPS
cd /opt  # o el directorio que prefieras
git clone https://github.com/dagorret/pylucy.git
cd pylucy

# 3. Iniciar todo (hace build automático la primera vez)
./deploy-testing.sh start

# 4. Crear superusuario
./deploy-testing.sh superuser

# 5. Ver información de acceso
./deploy-testing.sh info
```

¡Listo! Ya tienes PyLucy corriendo.

## 📱 Acceso a los Servicios

Después del deployment, tendrás acceso a:

### Aplicación Principal
- **URL**: `http://IP_SERVIDOR:8000`
- **Admin**: `http://IP_SERVIDOR:8000/admin`

### MailHog (Ver Emails de Prueba)
- **URL**: `http://IP_SERVIDOR:8025`
- Todos los emails que envíe la aplicación se verán aquí
- No se envían emails reales

### PgAdmin (Administrar Base de Datos)
- **URL**: `http://IP_SERVIDOR:5050`
- **Usuario**: `admin@unrc.edu.ar`
- **Contraseña**: `admin`

Para conectar a la BD desde PgAdmin:
- Host: `db`
- Port: `5432`
- Database: `pylucy`
- Username: `pylucy`
- Password: `pylucy`

## 🔧 Comandos Disponibles

```bash
# Iniciar servicios
./deploy-testing.sh start

# Detener servicios
./deploy-testing.sh stop

# Reiniciar servicios
./deploy-testing.sh restart

# Ver logs en tiempo real
./deploy-testing.sh logs

# Ver estado de servicios
./deploy-testing.sh status

# Mostrar URLs de acceso
./deploy-testing.sh info

# Crear superusuario
./deploy-testing.sh superuser

# Backup de base de datos
./deploy-testing.sh backup

# Abrir shell en el contenedor
./deploy-testing.sh shell

# Actualizar después de cambios en Git
git pull
./deploy-testing.sh update
```

## 📧 Configurar Correo de Prueba para Usuarios

Para que los usuarios de prueba puedan recibir emails:

1. Dale acceso a MailHog: `http://IP_SERVIDOR:8025`
2. Los emails enviados por la aplicación aparecerán allí
3. No necesitan configurar nada, solo acceder a la URL

**Ejemplo de email a enviar a testers:**

```
Hola,

Estás invitado a probar PyLucy Alfa 1.

Accesos:
- Aplicación: http://IP_SERVIDOR:8000
- Ver emails de prueba: http://IP_SERVIDOR:8025

Los emails que recibas de PyLucy NO llegarán a tu correo real.
Usa el link de MailHog para verlos.

Credenciales:
- Usuario: [tu_usuario]
- Contraseña: [tu_contraseña]

¡Gracias por probar!
```

## 🔌 Puertos Expuestos

El servidor expone estos puertos:
- `8000`: Django (aplicación web)
- `8025`: MailHog UI (ver emails)
- `1025`: MailHog SMTP (servidor de email)
- `5050`: PgAdmin (administrar BD)
- `5432`: PostgreSQL (acceso directo a BD)
- `6379`: Redis (cache y tareas)

Si tienes firewall, asegúrate de permitir al menos:
```bash
sudo ufw allow 8000/tcp  # Django
sudo ufw allow 8025/tcp  # MailHog
sudo ufw allow 5050/tcp  # PgAdmin (opcional)
```

## 📝 Configuración Actual

Esta configuración usa `.env.dev` que incluye:

- **Base de datos**: PostgreSQL (usuario/password: pylucy/pylucy)
- **Email**: MailHog (todos los emails quedan capturados)
- **SIAL/UTI**: Mock API (datos de prueba)
- **Moodle**: Sandbox de Moodle
- **Teams**: Credenciales de testing
- **Modo**: `ENVIRONMENT_MODE=testing` (prefijo "test-a")

Todo está configurado para pruebas internas, no hay datos sensibles.

## 🔄 Actualizar la Aplicación

Cuando hagas cambios en el código:

```bash
# En el servidor
cd /opt/pylucy
git pull
./deploy-testing.sh update
```

El comando `update` hace:
1. Pull del código
2. Rebuild de las imágenes Docker
3. Restart de los servicios
4. Ejecuta migraciones si hay

## 🗑️ Limpiar y Empezar de Cero

Si necesitas borrar todo y empezar de cero:

```bash
./deploy-testing.sh clean
./deploy-testing.sh start
./deploy-testing.sh superuser
```

⚠️ **CUIDADO**: `clean` elimina todos los datos de la base de datos.

## 🐛 Solución de Problemas

### Los servicios no inician

```bash
# Ver qué pasó
./deploy-testing.sh logs

# Verificar estado
./deploy-testing.sh status

# Reintentar
./deploy-testing.sh restart
```

### No puedo acceder desde mi navegador

1. Verificar que el firewall permita el puerto 8000
2. Usar la IP del servidor, no localhost
3. Verificar que los servicios estén corriendo:
   ```bash
   ./deploy-testing.sh status
   ```

### Los emails no aparecen en MailHog

1. Verificar que MailHog esté corriendo:
   ```bash
   docker compose -f docker-compose.testing.yml ps mailhog
   ```
2. Acceder a: `http://IP_SERVIDOR:8025`
3. Ver logs de MailHog:
   ```bash
   docker compose -f docker-compose.testing.yml logs mailhog
   ```

### Error de base de datos

```bash
# Ver logs de PostgreSQL
docker compose -f docker-compose.testing.yml logs db

# Reiniciar solo la base de datos
docker compose -f docker-compose.testing.yml restart db

# Ejecutar migraciones manualmente
docker compose -f docker-compose.testing.yml exec web python manage.py migrate
```

## 📊 Monitoreo

### Ver logs en tiempo real

```bash
./deploy-testing.sh logs
```

### Ver solo logs de Django

```bash
docker compose -f docker-compose.testing.yml logs -f web
```

### Ver logs de Celery (tareas asíncronas)

```bash
docker compose -f docker-compose.testing.yml logs -f celery
```

## 🔐 Seguridad

Para Alfa 1:
- ✅ Acceso solo por IP (sin dominio público aún)
- ✅ Contraseñas simples (es ambiente de testing)
- ✅ Datos de prueba (no hay datos reales)
- ✅ MailHog captura emails (no se envían reales)

Para Beta/Producción se configurará:
- 🔒 HTTPS con certificado SSL
- 🔒 Contraseñas fuertes
- 🔒 SMTP real
- 🔒 Firewall restrictivo

## 📞 Soporte

Si tienes problemas:

1. Ver logs: `./deploy-testing.sh logs`
2. Ver estado: `./deploy-testing.sh status`
3. Revisar este documento
4. Contactar al equipo de desarrollo

## 🎯 Próximos Pasos

Después de las pruebas alfa:

1. Recolectar feedback de usuarios
2. Corregir bugs encontrados
3. Preparar deployment de producción con:
   - HTTPS
   - SMTP real
   - Credenciales de producción
   - Monitoreo avanzado
