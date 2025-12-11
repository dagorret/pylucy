# Checklist de Deployment - PyLucy Fase Alfa

## Pre-Deployment (En tu máquina)

- [ ] **Código testeado** en entorno de desarrollo
- [ ] **Migraciones** aplicadas y verificadas
- [ ] **Requirements.txt** actualizado
- [ ] **Documentación** actualizada
- [ ] **Credenciales de prueba** removidas del código
- [ ] **.gitignore** incluye archivos sensibles (.env*, *.pyc, __pycache__)

---

## Preparación del Servidor

### Sistema

- [ ] **Ubuntu 20.04+** o Debian 11+ instalado
- [ ] **Docker** instalado (`docker --version`)
- [ ] **Docker Compose** instalado (`docker compose version`)
- [ ] **Puertos** 80 y 443 abiertos en firewall
- [ ] **Recursos mínimos**: 4GB RAM, 2 CPU cores, 20GB disco

### Usuario

- [ ] Usuario con **sudo** o permisos de Docker
- [ ] SSH configurado para acceso remoto

---

## Transferencia de Código

- [ ] Código **transferido** al servidor (Git o SCP)
- [ ] Ubicado en directorio apropiado (ej: `/home/usuario/pylucy`)
- [ ] Permisos correctos (`chmod +x prod.sh`)

---

## Configuración de Variables de Entorno

### Archivo .env.prod

- [ ] `.env.prod` creado desde `.env.prod.example`
- [ ] **SECRET_KEY** generada (única, segura, >50 caracteres)
- [ ] **DB_PASSWORD** configurada (contraseña segura para PostgreSQL)
- [ ] **ALLOWED_HOSTS** configurado con dominio del servidor

### SIAL/UTI

- [ ] **SIAL_BASE_URL** configurada (URL real de producción)
- [ ] **SIAL_BASIC_USER** configurado
- [ ] **SIAL_BASIC_PASS** configurada
- [ ] Credenciales **verificadas** (test de conexión)

### Teams/Azure AD

- [ ] **TEAMS_TENANT** configurado (GUID del tenant)
- [ ] **TEAMS_CLIENT_ID** configurado (GUID del app registration)
- [ ] **TEAMS_CLIENT_SECRET** configurado (secret generado)
- [ ] **TEAMS_DOMAIN** verificado (eco.unrc.edu.ar)
- [ ] App Registration tiene **permisos** correctos en Azure AD

### Moodle

- [ ] **MOODLE_BASE_URL** configurada (URL de Moodle institucional)
- [ ] **MOODLE_WSTOKEN** configurado (token de webservices)
- [ ] Token tiene **permisos** correctos en Moodle
- [ ] Webservices **habilitados** en Moodle

### Email (SMTP)

- [ ] **EMAIL_HOST** configurado (servidor SMTP institucional)
- [ ] **EMAIL_PORT** configurado (587 para TLS)
- [ ] **EMAIL_USE_TLS** = True
- [ ] **EMAIL_HOST_USER** configurado
- [ ] **EMAIL_HOST_PASSWORD** configurada
- [ ] Credenciales SMTP **verificadas** (test de envío)

### Modo de Operación

- [ ] **ENVIRONMENT_MODE** = production (o testing para fase alfa)
- [ ] **ACCOUNT_PREFIX** = a (o test-a para testing)

---

## Deployment

### Build y Inicio

- [ ] Ejecutar `./prod.sh`
- [ ] Esperar construcción de imágenes (~2 minutos)
- [ ] Verificar que todos los servicios están **healthy**:
  ```bash
  docker compose -f docker-compose.prod.yml ps
  ```

### Servicios Esperados

- [ ] `pylucy-db-prod` → **healthy**
- [ ] `pylucy-redis-prod` → **healthy**
- [ ] `pylucy-web-prod` → **healthy**
- [ ] `pylucy-celery-prod` → **healthy**
- [ ] `pylucy-celery-beat-prod` → **running**
- [ ] `pylucy-nginx-prod` → **healthy**

---

## Configuración Inicial

### Superusuario

- [ ] Superusuario **creado**:
  ```bash
  docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
  ```
- [ ] Login al admin **verificado**: http://servidor/admin

### Tareas Periódicas

- [ ] Tareas periódicas **configuradas**:
  ```bash
  docker compose -f docker-compose.prod.yml exec web python manage.py setup_periodic_tasks
  ```

### Configuración del Sistema (Admin)

- [ ] Ir a: **Alumnos > Configuración del Sistema**
- [ ] **Procesamiento en Lotes** configurado:
  - batch_size: 20
  - rate_limit_teams: 10
  - rate_limit_moodle: 30
- [ ] **Ingesta de Preinscriptos** configurada:
  - Día inicio y fin según calendario académico
  - Frecuencia: 3600 segundos (1 hora)
- [ ] **Ingesta de Aspirantes** configurada (si aplica)
- [ ] **Ingesta de Ingresantes** configurada (si aplica)

---

## Testing Post-Deployment

### Conectividad Básica

- [ ] Admin accesible: http://servidor/admin/login/
- [ ] Archivos estáticos cargan correctamente (CSS, JS, imágenes)
- [ ] No hay errores 500 en navegador

### Servicios Externos

- [ ] **SIAL** - Test de conexión:
  ```bash
  docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "
  from alumnos.services.ingesta import SIALClient
  client = SIALClient()
  listas = client.fetch_listas('preinscriptos', n=1)
  print(f'✓ SIAL OK: {len(listas)} registros')
  "
  ```

- [ ] **Teams** - Test de autenticación:
  ```bash
  docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "
  from alumnos.services.teams_service import TeamsService
  ts = TeamsService()
  token = ts._get_token()
  print(f'✓ Teams OK' if token else '✗ Teams ERROR')
  "
  ```

- [ ] **Email** - Test de envío (verificar logs):
  ```bash
  docker compose -f docker-compose.prod.yml logs -f web | grep -i email
  ```

### Ingesta Manual de Prueba

- [ ] Ingestar 5 registros de prueba:
  ```bash
  docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "
  from alumnos.services.ingesta import ingerir_desde_sial
  created, updated, errors = ingerir_desde_sial('preinscriptos', n=5)
  print(f'Creados: {created}, Actualizados: {updated}, Errores: {len(errors)}')
  "
  ```

- [ ] Verificar en Admin que los alumnos aparecen:
  - http://servidor/admin/alumnos/alumno/

### Workflows de Prueba

- [ ] Crear cuenta Teams para 1 alumno (manual desde admin):
  - Seleccionar alumno
  - Actions → "Crear cuenta Teams"
  - Verificar logs: `docker compose -f docker-compose.prod.yml logs -f celery`

- [ ] Verificar tarea en tabla **Tareas Asíncronas**:
  - http://servidor/admin/alumnos/tarea/

- [ ] Verificar logs del sistema:
  - http://servidor/admin/alumnos/log/

### Tareas Periódicas

- [ ] Verificar que Celery Beat está programando tareas:
  ```bash
  docker compose -f docker-compose.prod.yml logs celery-beat | tail -50
  ```

- [ ] Esperar a la próxima ejecución automática (según frecuencia configurada)
- [ ] Verificar en logs que la tarea se ejecutó

---

## Monitoreo

### Logs

- [ ] Logs de **Web** sin errores críticos:
  ```bash
  docker compose -f docker-compose.prod.yml logs web | grep -i error
  ```

- [ ] Logs de **Celery** sin errores críticos:
  ```bash
  docker compose -f docker-compose.prod.yml logs celery | grep -i error
  ```

- [ ] Logs de **Nginx** muestran requests exitosos:
  ```bash
  docker compose -f docker-compose.prod.yml logs nginx | tail -50
  ```

### Healthchecks

- [ ] Todos los servicios reportan **healthy**:
  ```bash
  docker compose -f docker-compose.prod.yml ps
  ```

### Base de Datos

- [ ] PostgreSQL acepta conexiones:
  ```bash
  docker compose -f docker-compose.prod.yml exec db pg_isready -U pylucy
  ```

- [ ] Backup de BD funciona:
  ```bash
  docker compose -f docker-compose.prod.yml exec db pg_dump -U pylucy pylucy > test_backup.sql
  ls -lh test_backup.sql
  ```

---

## Seguridad

- [ ] **DEBUG=False** en `.env.prod`
- [ ] **SECRET_KEY** es única y segura (no la de desarrollo)
- [ ] **.env.prod** NO está en Git (verificar `.gitignore`)
- [ ] Credenciales NO están hardcodeadas en código
- [ ] Firewall configurado (solo puertos 22, 80, 443 abiertos)

---

## Backup

- [ ] Script de backup automático configurado (opcional para fase alfa)
- [ ] Backup manual ejecutado y verificado:
  ```bash
  docker compose -f docker-compose.prod.yml exec db pg_dump -U pylucy pylucy > backup_inicial.sql
  ```
- [ ] Backup guardado en **ubicación segura** (fuera del servidor)

---

## Documentación para el Equipo

- [ ] **DEPLOYMENT.md** revisado y actualizado
- [ ] Credenciales compartidas de forma segura (no por email/chat)
- [ ] Equipo tiene acceso SSH al servidor
- [ ] Equipo sabe cómo ver logs y reiniciar servicios
- [ ] Manual de usuario básico disponible (si aplica)

---

## Entrega al Cliente/Usuario Final

- [ ] Demo realizada mostrando funcionalidades
- [ ] Usuarios de prueba creados
- [ ] Calendario de ingesta configurado según ciclo académico
- [ ] Contacto de soporte definido
- [ ] Plan de monitoreo acordado

---

## Post-Deployment

### Primera Semana

- [ ] Monitorear logs diariamente
- [ ] Verificar ejecución de tareas periódicas
- [ ] Validar que ingestas automáticas funcionan
- [ ] Recolectar feedback de usuarios

### Primera Mes

- [ ] Revisar performance (CPU, RAM, disco)
- [ ] Optimizar configuración de batching si es necesario
- [ ] Implementar alertas automáticas (opcional)
- [ ] Configurar SSL/HTTPS (si no está hecho)

---

## Checklist Final

- [ ] ✅ Sistema **desplegado** y accesible
- [ ] ✅ Todos los servicios **healthy**
- [ ] ✅ Ingesta automática **funcionando**
- [ ] ✅ Workflows (Teams/Email) **probados**
- [ ] ✅ Usuarios pueden **acceder al admin**
- [ ] ✅ Backup inicial **realizado**
- [ ] ✅ Documentación **completa**
- [ ] ✅ Equipo **capacitado**

---

**Fecha de deployment**: _______________

**Responsable**: _______________

**Observaciones**: _______________________________________________

_________________________________________________________________

_________________________________________________________________
