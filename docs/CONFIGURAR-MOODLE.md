# Configurar Moodle en PyLucy

## ✅ Sí, puedes cambiar la URL y token de Moodle desde el Admin

PyLucy permite configurar Moodle de **dos formas**:

1. **Desde el Django Admin** (Recomendado) ✅
2. Desde variables de entorno (Respaldo)

## 🎯 Configurar desde Django Admin

### Paso 1: Acceder a Configuración del Sistema

1. Ir a: `http://IP_SERVIDOR:8000/admin/`
2. Login con: `AdminFCE.16` / `Milei2027!` (o `admin` / `admin`)
3. En el menú lateral: **Alumnos** → **Configuración del Sistema**
4. Click en la única configuración existente (se crea automáticamente)

### Paso 2: Configurar Moodle

En la sección **"Configuración de Moodle"**:

```
┌─────────────────────────────────────────────────────────┐
│ Configuración de Moodle                                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Moodle base URL:                                        │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ https://moodle.eco.unrc.edu.ar                      │ │
│ └─────────────────────────────────────────────────────┘ │
│ URL base de Moodle. Si está vacío, usa variable de     │
│ entorno                                                  │
│                                                          │
│ Moodle wstoken:                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ abc123def456ghi789jkl012mno345pqr678                │ │
│ └─────────────────────────────────────────────────────┘ │
│ Token de Moodle WebServices. Si está vacío, usa        │
│ variable de entorno                                      │
│                                                          │
│ Rate limit moodle:                                      │
│ ┌──────┐                                                │
│ │  30  │ requests por minuto                            │
│ └──────┘                                                │
│                                                          │
└─────────────────────────────────────────────────────────┘

              [ Guardar ]  [ Guardar y continuar editando ]
```

### Paso 3: Guardar y Reiniciar (Opcional)

Los cambios se aplican **inmediatamente** (no requiere reiniciar).

Si quieres asegurarte:
```bash
docker compose -f docker-compose.testing.yml restart celery
```

---

## 🔧 Valores Recomendados

### Para Testing (Sandbox de Moodle):
```
Moodle base URL: https://sandbox.moodledemo.net
Moodle wstoken: (dejar vacío o token de sandbox)
Rate limit moodle: 30
```

### Para Testing Real / Producción:
```
Moodle base URL: https://moodle.eco.unrc.edu.ar
Moodle wstoken: tu_token_real_aquí
Rate limit moodle: 30
```

---

## 🔑 Cómo Obtener el Token de Moodle

### Paso 1: Habilitar Web Services en Moodle

1. Login como administrador en Moodle
2. Ir a: **Administración del sitio** → **Plugins** → **Servicios web** → **Resumen**
3. Habilitar servicios web si no lo están

### Paso 2: Crear un Usuario de Servicio

1. **Administración del sitio** → **Usuarios** → **Cuentas** → **Agregar nuevo usuario**
2. Datos sugeridos:
   - Username: `pylucy_webservice`
   - Nombre: `PyLucy`
   - Apellido: `WebService`
   - Email: `pylucy@eco.unrc.edu.ar`
   - Autenticación: Manual

### Paso 3: Asignar Capacidades

1. **Administración del sitio** → **Usuarios** → **Permisos** → **Definir roles**
2. Crear un rol nuevo: "PyLucy WebService"
3. Asignar capacidades:
   - `moodle/user:create` (crear usuarios)
   - `moodle/course:enrol` (enrollar usuarios)
   - `webservice/rest:use` (usar webservices REST)

### Paso 4: Crear Servicio Web

1. **Administración del sitio** → **Servidor** → **Servicios web** → **Servicios externos**
2. Agregar nuevo servicio:
   - Nombre: `PyLucy Integration`
   - Nombre corto: `pylucy`
   - Habilitado: Sí
3. Agregar funciones:
   - `core_user_create_users`
   - `enrol_manual_enrol_users`
   - `core_course_get_courses`

### Paso 5: Generar Token

1. **Administración del sitio** → **Servidor** → **Servicios web** → **Gestionar tokens**
2. Crear token para el usuario `pylucy_webservice`
3. Servicio: `PyLucy Integration`
4. Copiar el token generado (ej: `abc123def456...`)

### Paso 6: Configurar en PyLucy

Pegar el token en Django Admin → Configuración → Moodle wstoken

---

## 🔄 Orden de Prioridad

PyLucy busca la configuración en este orden:

```
1. Base de Datos (Django Admin)
   ↓ (si no existe o está vacío)
2. Variables de Entorno (.env.dev)
   ↓ (si no existe)
3. Default hardcodeado (sandbox)
```

### Ejemplo:

```python
# En Django Admin:
Moodle base URL: https://moodle.eco.unrc.edu.ar  ← USAR ESTE

# En .env.dev:
MOODLE_BASE_URL=https://sandbox.moodledemo.net   ← Ignorado

# Resultado: Usa https://moodle.eco.unrc.edu.ar
```

---

## 🧪 Probar la Configuración

### Desde Django Admin:

1. Ir a **Alumnos** → **Preinscriptos**
2. Seleccionar un preinscripto
3. Click en **Actions** → **Procesar preinscripto seleccionado**
4. Ver logs para confirmar que usa la URL correcta

### Desde Terminal:

```bash
# Ver configuración actual
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
from alumnos.utils.config import get_moodle_base_url, get_moodle_wstoken
print('URL:', get_moodle_base_url())
print('Token:', get_moodle_wstoken()[:20] + '...' if get_moodle_wstoken() else 'No configurado')
"
```

### Logs de Celery:

```bash
# Ver si se conecta a Moodle
docker compose -f docker-compose.testing.yml logs -f celery | grep -i moodle
```

---

## ⚙️ Configuración Avanzada

### Rate Limiting

**Rate limit moodle**: Controla cuántos requests por minuto se hacen a Moodle.

- **Bajo (10-20)**: Servidor Moodle lento o limitado
- **Medio (30-40)**: Recomendado para producción
- **Alto (50+)**: Solo si Moodle puede manejarlo

### Cambiar otros parámetros:

En la misma pantalla de Configuración:

- **Batch size**: Cuántos estudiantes procesar en cada lote
- **Rate limit Teams**: Límite de requests a Microsoft Teams
- **Ingesta automática**: Fechas y frecuencia de sincronización con SIAL

---

## 🛡️ Seguridad

### ⚠️ El token de Moodle es SENSIBLE:

- ✅ Guardarlo en la base de datos (Django Admin) está OK
- ✅ La base de datos está protegida
- ❌ NO compartir el token
- ❌ NO exponerlo en logs públicos
- ❌ NO subirlo a Git (si lo pones en .env.prod)

### Rotar el token:

Si el token se compromete:
1. Ir a Moodle Admin → Gestionar tokens
2. Eliminar el token viejo
3. Crear uno nuevo
4. Actualizar en Django Admin → Configuración

---

## 📊 Diferencia con Variables de Entorno

### Variables de Entorno (.env.dev):
- ✅ Se cargan al iniciar el contenedor
- ❌ Requieren reiniciar para cambiar
- ❌ Más difícil de cambiar (editar archivo, rebuild)
- ✅ Sirven como valores por defecto

### Django Admin (Base de Datos):
- ✅ Se pueden cambiar en caliente
- ✅ No requiere reiniciar servicios
- ✅ Interfaz web fácil de usar
- ✅ **Tiene prioridad** sobre variables de entorno

---

## 🎯 Resumen

**Pregunta**: ¿Puedo cambiar la URL y token de Moodle desde la configuración?

**Respuesta**: ✅ **SÍ**

**Dónde**: Django Admin → Alumnos → Configuración del Sistema

**Requiere reiniciar**: ❌ NO (los cambios se aplican inmediatamente)

**Tiene prioridad sobre .env.dev**: ✅ SÍ

**Es la forma recomendada**: ✅ SÍ

---

## 📝 Checklist

Al configurar Moodle:

- [ ] Obtener token de Moodle (o usar sandbox)
- [ ] Ir a Django Admin → Configuración
- [ ] Poner URL: `https://moodle.eco.unrc.edu.ar`
- [ ] Poner token obtenido
- [ ] Configurar rate limit (30 recomendado)
- [ ] Guardar configuración
- [ ] Probar procesando un preinscripto de prueba
- [ ] Verificar logs que use la URL correcta

---

## 🆘 Troubleshooting

### "No puedo ver Configuración en el admin"
- Verificar que tengas permisos de superuser
- Verificar que las migraciones estén aplicadas: `docker compose -f docker-compose.testing.yml exec web python manage.py migrate`

### "Los cambios no se aplican"
- Los cambios son inmediatos, pero si procesaste antes de cambiar, los jobs en cola usan la config vieja
- Reinicia celery: `docker compose -f docker-compose.testing.yml restart celery`

### "Sigue usando la URL de .env.dev"
- Verificar que hayas guardado en Django Admin
- Verificar que el campo NO esté vacío
- Usar el comando de terminal arriba para ver qué URL está usando
