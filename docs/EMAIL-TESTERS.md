# Plantilla de Email para Testers - PyLucy Alfa 1

## Email de Invitación a Pruebas

```
Asunto: Invitación - Pruebas PyLucy Alfa 1

Hola [Nombre],

Estás invitado/a a participar en las pruebas alfa de PyLucy, el sistema de gestión
de estudiantes y sincronización con Microsoft Teams.

═══════════════════════════════════════════════════════════════════════════════

📱 ACCESOS AL SISTEMA

Aplicación Web:
  http://[IP_SERVIDOR]:8000

Panel de Administración:
  http://[IP_SERVIDOR]:8000/admin

═══════════════════════════════════════════════════════════════════════════════

👤 TUS CREDENCIALES

Usuario: [usuario_del_tester]
Contraseña: [contraseña_del_tester]

═══════════════════════════════════════════════════════════════════════════════

📧 IMPORTANTE - EMAILS DE PRUEBA

Los emails que envíe PyLucy NO llegarán a tu correo real.

Para ver los emails que te envía el sistema, accede a MailHog:
  http://[IP_SERVIDOR]:8025

Todos los emails que genere la aplicación (notificaciones, confirmaciones, etc.)
aparecerán en esta interfaz web.

═══════════════════════════════════════════════════════════════════════════════

🎯 QUÉ PROBAR

1. Inicio de sesión
2. Navegación por el sistema
3. Gestión de estudiantes
4. Sincronización con Teams (modo testing)
5. Búsqueda y filtros
6. Carga de datos desde SIAL/UTI
7. Cualquier funcionalidad que encuentres

═══════════════════════════════════════════════════════════════════════════════

🐛 REPORTAR PROBLEMAS

Si encuentras algún error o problema:

1. Anota qué estabas haciendo cuando ocurrió
2. Si hay mensaje de error, cópialo completo
3. Si es posible, toma una captura de pantalla
4. Envíame un email con los detalles a: [tu_email]

También puedes reportar sugerencias de mejora.

═══════════════════════════════════════════════════════════════════════════════

⚠️ CONSIDERACIONES

- Esto es una versión ALFA, pueden haber errores
- Los datos son de prueba, no son reales
- El sistema está en modo "testing" (usa prefijo "test-a" para cuentas)
- Tus comentarios son muy valiosos para mejorar el sistema

═══════════════════════════════════════════════════════════════════════════════

📅 PLAZO DE PRUEBAS

Fecha de inicio: [FECHA_INICIO]
Fecha límite para feedback: [FECHA_FIN]

═══════════════════════════════════════════════════════════════════════════════

¡Muchas gracias por tu colaboración!

Saludos,
[Tu nombre]
[Tu cargo/posición]
```

## Email Corto (Versión Simplificada)

```
Asunto: PyLucy Alfa - Acceso de prueba

Hola [Nombre],

Acceso a PyLucy Alfa 1:

🌐 App: http://[IP_SERVIDOR]:8000
👤 Usuario: [usuario]
🔑 Password: [contraseña]

📧 Ver emails de prueba: http://[IP_SERVIDOR]:8025
(Los emails NO llegarán a tu correo real, usa este link)

Prueba lo que quieras y reporta cualquier error o sugerencia.

¡Gracias!
[Tu nombre]
```

## Lista de Verificación para Enviar

Antes de enviar el email a los testers:

- [ ] Reemplazar `[IP_SERVIDOR]` con la IP real del servidor
- [ ] Crear las credenciales de cada tester en Django Admin
- [ ] Reemplazar `[usuario_del_tester]` y `[contraseña_del_tester]`
- [ ] Agregar fechas de inicio y fin de pruebas
- [ ] Poner tu email de contacto
- [ ] Verificar que MailHog esté accesible
- [ ] Verificar que la aplicación esté corriendo
- [ ] Hacer una prueba tú mismo antes de invitar

## Crear Usuarios Testers

Desde el servidor:

```bash
# Opción 1: Desde la interfaz web
# Ve a http://IP_SERVIDOR:8000/admin/auth/user/add/

# Opción 2: Desde consola
./deploy-testing.sh shell
python manage.py createsuperuser  # Si necesitas admin

# O crear usuario normal con Django shell
./deploy-testing.sh shell
python manage.py shell
```

```python
from django.contrib.auth.models import User

# Crear usuario tester
user = User.objects.create_user(
    username='tester1',
    email='tester1@eco.unrc.edu.ar',
    password='TestPass123',
    first_name='Tester',
    last_name='Uno'
)

# Si quiere acceso al admin
user.is_staff = True
user.save()
```

## Después de las Pruebas

Email de agradecimiento:

```
Asunto: PyLucy Alfa - Gracias por tu participación

Hola [Nombre],

Muchas gracias por participar en las pruebas de PyLucy Alfa 1.

Tu feedback ha sido muy valioso para mejorar el sistema.

═══════════════════════════════════════════════════════════════════════════════

📊 PRÓXIMOS PASOS

Basándonos en los comentarios recibidos, trabajaremos en:
- [Lista de mejoras identificadas]
- [Bugs a corregir]
- [Nuevas funcionalidades]

═══════════════════════════════════════════════════════════════════════════════

Te mantendremos informado sobre:
- Correcciones implementadas
- Próxima versión Beta
- Fecha estimada de producción

═══════════════════════════════════════════════════════════════════════════════

¡Gracias nuevamente!

Saludos,
[Tu nombre]
```

## URLs de Acceso Rápido

Para tu referencia:

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| Aplicación | http://[IP]:8000 | Usuario tester |
| Admin Django | http://[IP]:8000/admin | Superuser |
| MailHog (emails) | http://[IP]:8025 | - |
| PgAdmin (BD) | http://[IP]:5050 | admin@unrc.edu.ar / admin |

## Monitoreo Durante Pruebas

Comandos útiles mientras los testers prueban:

```bash
# Ver logs en tiempo real
./deploy-testing.sh logs

# Ver solo errores
docker compose -f docker-compose.testing.yml logs | grep -i error

# Ver cuántos emails se enviaron
curl http://IP_SERVIDOR:8025/api/v2/messages | jq '. | length'

# Ver estado de servicios
./deploy-testing.sh status
```
