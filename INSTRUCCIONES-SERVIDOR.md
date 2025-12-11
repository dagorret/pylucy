# Instrucciones para Actualizar el Servidor

## Credenciales por Defecto

Cuando arranques el contenedor, se creará automáticamente un superuser:

- **Usuario:** `admin`
- **Contraseña:** `admin`
- **URL Admin:** `http://TU_IP:8000/admin/`

## Para Actualizar el Servidor (179.43.116.154)

Ejecuta estos comandos en el servidor:

```bash
cd /home/motorola/pylucy

# 1. Actualizar código desde GitHub
git pull

# 2. Rebuild de la imagen (incluye el nuevo entrypoint)
docker compose -f docker-compose.testing.yml build

# 3. Detener contenedores
docker compose -f docker-compose.testing.yml down

# 4. Iniciar todo de nuevo
docker compose -f docker-compose.testing.yml up -d

# 5. Ver logs para verificar que todo arrancó bien
docker compose -f docker-compose.testing.yml logs -f web
```

## Qué hace el nuevo entrypoint automáticamente:

Cada vez que arranque el contenedor web, ejecutará:

1. ✅ Esperar a que la base de datos esté lista
2. ✅ Ejecutar migraciones (`migrate`)
3. ✅ Colectar archivos estáticos (`collectstatic`)
4. ✅ Crear superuser `admin/admin` si no existe
5. ✅ Iniciar el servidor Django

## Verificar que todo funciona:

Después de arrancar, visita:

- **Página principal:** `http://179.43.116.154:8000/`
  - Debería verse con todos los estilos CSS aplicados

- **Test CSS:** `http://179.43.116.154:8000/test-css/`
  - Debería mostrar fondo azul con texto blanco

- **Admin:** `http://179.43.116.154:8000/admin/`
  - Usuario: `admin`
  - Contraseña: `admin`

- **CSS directo:** `http://179.43.116.154:8000/static/css/tailwind.css`
  - Debería mostrar el archivo CSS (no un 404)

## Si algo falla:

```bash
# Ver logs completos
docker compose -f docker-compose.testing.yml logs

# Ver logs solo del web
docker compose -f docker-compose.testing.yml logs web

# Reiniciar un servicio específico
docker compose -f docker-compose.testing.yml restart web

# Entrar al contenedor para debugging
docker compose -f docker-compose.testing.yml exec web bash
```

## Comandos útiles:

```bash
# Ver estado de servicios
docker compose -f docker-compose.testing.yml ps

# Ver todos los usuarios en la BD
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django.contrib.auth.models import User
for u in User.objects.all():
    print(f'{u.username} - {u.email} - Superuser: {u.is_superuser}')
"

# Resetear contraseña de admin
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='admin')
user.set_password('admin')
user.save()
print('Contraseña reseteada: admin/admin')
"
```

## ¿Por qué era necesario esto?

Antes, cuando iniciabas el contenedor:
- Los archivos estáticos NO se copiaban automáticamente
- El CSS no estaba disponible en `/static/`
- La página se veía sin estilos

Ahora, con el entrypoint:
- Todo se configura automáticamente al arrancar
- No necesitas ejecutar comandos manuales
- El CSS y todos los archivos estáticos están disponibles
