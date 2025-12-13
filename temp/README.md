# Moodle Stats - Sistema de Exportación y Análisis de Datos

Sistema Django para exportar, importar y analizar datos de Moodle con interfaz administrativa.

## 📋 Características

- ✅ Exportación de datos desde Moodle MySQL a archivos NDJSON
- ✅ Importación de datos a Django para análisis
- ✅ Interfaz administrativa completa
- ✅ Exportación individual a Excel por tabla
- ✅ Datos persistentes en volúmenes Docker
- ✅ 94,767+ registros de 10 tablas de Moodle

## 🗂️ Tablas Soportadas

1. **courses** - Cursos (306 registros)
2. **categories** - Categorías (21 registros)
3. **enrol** - Métodos de inscripción (830 registros)
4. **user_enrolments** - Inscripciones de usuarios (17,384 registros)
5. **users** - Usuarios (4,479 registros)
6. **groups** - Grupos (615 registros)
7. **groups_members** - Miembros de grupos (18,041 registros)
8. **user_lastaccess** - Últimos accesos (16,095 registros)
9. **role_assignments** - Asignaciones de roles (17,521 registros)
10. **context** - Contextos (19,475 registros)

## 🚀 Instalación y Configuración

### Requisitos Previos

- Docker y Docker Compose
- Acceso a la base de datos de Moodle (MySQL/MariaDB)
- Puerto 8008 disponible

### Configuración Inicial

1. **Clonar/Descargar el proyecto**
```bash
cd ~/work/msp
```

2. **Configurar variables de entorno**

Editar `docker-compose.yml`:
```yaml
environment:
  - MOODLE_DB_HOST=172.17.0.1  # IP del gateway Docker
  - MOODLE_DB_PORT=3306
  - MOODLE_DB_NAME=app3ecounrcedu_moodle
  - MOODLE_DB_USER=app3ecounrcedu_moodle
  - MOODLE_DB_PASSWORD=Iphone#162024
  - MOODLE_DB_PREFIX=mdl_
```

3. **Configurar permisos de MariaDB**

```bash
# Editar configuración de MariaDB
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf

# Cambiar:
bind-address = 0.0.0.0

# Reiniciar MariaDB
sudo systemctl restart mariadb

# Dar permisos al usuario
mysql -u root -p
```

```sql
GRANT ALL PRIVILEGES ON app3ecounrcedu_moodle.* TO 'app3ecounrcedu_moodle'@'172.17.%' IDENTIFIED BY 'Iphone#162024';
FLUSH PRIVILEGES;
EXIT;
```

4. **Iniciar el contenedor**

```bash
docker compose up -d
```

5. **Crear superusuario**

```bash
docker exec -it moodle_stats_web python manage.py createsuperuser
```

## 📊 Uso del Sistema

### Acceso al Admin

```
http://v.eco.unrc.edu.ar:8008/admin/
```

### Comandos Principales

#### Exportar datos desde Moodle

```bash
# Exportar todas las tablas
docker exec -it moodle_stats_web python manage.py export_moodle --tables all

# Exportar tablas específicas
docker exec -it moodle_stats_web python manage.py export_moodle --tables courses,users
```

Los archivos NDJSON se guardan en: `~/work/msp/data/exports/*.ndjson`

#### Importar datos a Django

```bash
# Importar todas las tablas (limpiando datos previos)
docker exec -it moodle_stats_web python manage.py import_moodle --tables all --clear

# Importar sin limpiar (agregar datos)
docker exec -it moodle_stats_web python manage.py import_moodle --tables all

# Importar tablas específicas
docker exec -it moodle_stats_web python manage.py import_moodle --tables courses,users --clear
```

### Exportar a Excel desde el Admin

1. Acceder a cualquier tabla en el admin
2. Seleccionar los registros que deseas exportar
3. En el menú "Acción", elegir **📊 Exportar a Excel**
4. Click en "Ir"
5. Se descargará un archivo Excel con los datos seleccionados

## 📁 Estructura de Archivos

```
~/work/msp/
├── data/                          # Datos persistentes
│   ├── db.sqlite3                # Base de datos Django
│   ├── exports/                  # Archivos NDJSON exportados
│   │   ├── courses.ndjson
│   │   ├── users.ndjson
│   │   └── ...
│   └── django.log               # Logs de la aplicación
├── moodledata/                   # App Django
│   ├── admin.py                 # Configuración del admin
│   ├── models.py                # Modelos de datos
│   └── management/commands/     # Comandos personalizados
│       ├── export_moodle.py
│       └── import_moodle.py
├── moodlestats/                 # Configuración Django
│   ├── settings.py
│   └── urls.py
├── templates/                   # Templates HTML
├── docker-compose.yml           # Configuración Docker
├── Dockerfile
└── requirements.txt

```

## 🔧 Mantenimiento

### Ver logs del contenedor

```bash
docker logs -f moodle_stats_web
```

### Reiniciar el servicio

```bash
docker compose restart
```

### Detener el servicio

```bash
docker compose down
```

### Backup de datos

```bash
# Backup de la base de datos Django
cp data/db.sqlite3 data/db.sqlite3.backup

# Backup de archivos NDJSON
tar -czf exports-backup-$(date +%Y%m%d).tar.gz data/exports/
```

### Restaurar datos

```bash
# Restaurar base de datos
cp data/db.sqlite3.backup data/db.sqlite3

# Restaurar exports
tar -xzf exports-backup-YYYYMMDD.tar.gz
```

## 📈 Flujo de Trabajo Típico

1. **Exportar datos actualizados desde Moodle:**
   ```bash
   docker exec -it moodle_stats_web python manage.py export_moodle --tables all
   ```

2. **Importar a Django (actualizar):**
   ```bash
   docker exec -it moodle_stats_web python manage.py import_moodle --tables all --clear
   ```

3. **Analizar en el Admin:**
   - Filtrar por categorías, fechas, estados
   - Buscar usuarios, cursos específicos
   - Generar reportes

4. **Exportar resultados a Excel:**
   - Seleccionar registros
   - Usar acción "Exportar a Excel"

## 🗄️ Persistencia de Datos

Todos los datos son persistentes en volúmenes Docker:

- **Base de datos Django:** `~/work/msp/data/db.sqlite3`
- **Archivos NDJSON:** `~/work/msp/data/exports/`
- **Logs:** `~/work/msp/data/django.log`

Los datos **NO se pierden** al reiniciar el contenedor.

## 🔒 Configuración de Red

El contenedor accede a Moodle MySQL usando:
- **IP Gateway Docker:** `172.17.0.1`
- Esta IP es fija mientras uses Docker en este servidor
- Permite que el contenedor acceda a servicios del host

## ⚙️ Variables de Entorno Importantes

| Variable | Descripción | Valor Default |
|----------|-------------|---------------|
| `MOODLE_DB_HOST` | Host de MySQL Moodle | `172.17.0.1` |
| `MOODLE_DB_PORT` | Puerto de MySQL | `3306` |
| `MOODLE_DB_NAME` | Nombre BD Moodle | - |
| `MOODLE_DB_USER` | Usuario MySQL | - |
| `MOODLE_DB_PASSWORD` | Contraseña MySQL | - |
| `MOODLE_DB_PREFIX` | Prefijo tablas | `mdl_` |
| `DEBUG` | Modo debug Django | `True` |

## 🐛 Troubleshooting

### Error: "Can't connect to MySQL server"

**Solución:**
1. Verificar que MariaDB esté escuchando en `0.0.0.0`
2. Verificar permisos del usuario desde `172.17.%`
3. Verificar firewall del servidor

### Error: "No such table: moodledata_course"

**Solución:**
```bash
docker exec -it moodle_stats_web python manage.py migrate
```

### El contenedor no inicia

**Solución:**
```bash
docker logs moodle_stats_web  # Ver el error
docker compose down
docker compose up -d --build  # Reconstruir
```

## 📝 Notas Importantes

- Los timestamps en Moodle son **Unix timestamps** (segundos desde 1970)
- Los archivos NDJSON usan **UTF-8** encoding
- La importación usa `bulk_create` con `ignore_conflicts=True` (evita duplicados)
- La exportación a Excel tiene límite de **50 caracteres** por celda en ancho de columna

## 🚀 Próximas Mejoras

- [ ] Gráficos y estadísticas en el admin
- [ ] Reportes personalizados
- [ ] Sincronización automática (cron)
- [ ] API REST para consultas
- [ ] Dashboard con métricas

## 📧 Soporte

Para problemas o consultas, revisar los logs:

```bash
docker logs -f moodle_stats_web
tail -f data/django.log
```

## 📜 Licencia

Proyecto interno - Universidad Nacional de Río Cuarto
