# PyLucy - Deployment Rápido (Fase Alfa)

## Inicio Rápido en 5 Pasos

### 1. Transferir código al servidor

```bash
# Opción A: Git
git clone https://github.com/tu-org/pylucy.git
cd pylucy

# Opción B: SCP (desde tu máquina)
scp -r /home/carlos/work/pylucy usuario@servidor:/home/usuario/
ssh usuario@servidor
cd pylucy
```

### 2. Configurar variables de entorno

```bash
# Copiar plantilla
cp .env.prod.example .env.prod

# Editar con tus credenciales
nano .env.prod
```

**Mínimo a configurar:**
- `SECRET_KEY` (generar con: `python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `DB_PASSWORD`
- `ALLOWED_HOSTS`
- `TEAMS_TENANT`, `TEAMS_CLIENT_ID`, `TEAMS_CLIENT_SECRET`
- `MOODLE_BASE_URL`, `MOODLE_WSTOKEN`
- `SIAL_BASE_URL`, `SIAL_BASIC_USER`, `SIAL_BASIC_PASS`

### 3. Ejecutar deployment

```bash
./prod.sh
```

Espera ~2 minutos mientras construye las imágenes y levanta servicios.

### 4. Crear usuario administrador

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 5. Acceder al sistema

```
http://servidor.unrc.edu.ar/admin
```

---

## Verificación Post-Deployment

```bash
# Ver estado de servicios
docker compose -f docker-compose.prod.yml ps

# Ver logs
docker compose -f docker-compose.prod.yml logs -f
```

**Servicios esperados:**
- ✅ pylucy-db-prod (healthy)
- ✅ pylucy-redis-prod (healthy)
- ✅ pylucy-web-prod (healthy)
- ✅ pylucy-celery-prod (healthy)
- ✅ pylucy-celery-beat-prod (running)
- ✅ pylucy-nginx-prod (healthy)

---

## Configuración Inicial en el Admin

1. Ir a: **Alumnos > Configuración del Sistema**

2. Configurar **Procesamiento en Lotes**:
   - batch_size: 20
   - rate_limit_teams: 10
   - rate_limit_moodle: 30

3. Configurar **Ingesta de Preinscriptos**:
   - Día inicio: (fecha de inicio del período de inscripción)
   - Día fin: (fecha de fin del período)
   - Frecuencia: 3600 (cada 1 hora)

4. **Setup de tareas periódicas**:
   ```bash
   docker compose -f docker-compose.prod.yml exec web python manage.py setup_periodic_tasks
   ```

---

## Test Rápido

```bash
# Ingestar 5 preinscriptos de prueba
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "
from alumnos.services.ingesta import ingerir_desde_sial
created, updated, errors = ingerir_desde_sial('preinscriptos', n=5)
print(f'✓ Creados: {created}, Actualizados: {updated}')
"
```

---

## Comandos Útiles

```bash
# Ver logs en tiempo real
docker compose -f docker-compose.prod.yml logs -f

# Reiniciar servicios
docker compose -f docker-compose.prod.yml restart

# Detener todo
docker compose -f docker-compose.prod.yml down

# Acceder a shell de Django
docker compose -f docker-compose.prod.yml exec web python manage.py shell
```

---

## Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| Error 502 Bad Gateway | `docker compose -f docker-compose.prod.yml restart web` |
| Can't connect to database | Verificar `DB_PASSWORD` en `.env.prod` |
| Tareas no se ejecutan | `docker compose -f docker-compose.prod.yml restart celery celery-beat` |
| Static files no cargan | `docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput` |

---

## Documentación Completa

Ver: `/doc/DEPLOYMENT.md`

---

## Soporte

- **Issues**: https://github.com/tu-org/pylucy/issues
- **Documentación**: `/doc/`
- **Logs**: `docker compose -f docker-compose.prod.yml logs -f`
