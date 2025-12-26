# 📋 Resumen de Actualización - PyLucy

**Fecha:** 26 de diciembre de 2025
**Versión:** Actualización de credenciales y plantillas de email

---

## ✅ Cambios Implementados

### 1. Generación de Passwords Aleatorias y Seguras

**Archivo:** `src/alumnos/services/teams_service.py:479-514`

- ✅ Passwords completamente aleatorias (16 caracteres)
- ✅ Cumple con estándares de Microsoft:
  - 4 mayúsculas
  - 4 minúsculas
  - 4 dígitos
  - 4 símbolos especiales (!@#$%^&*)
- ✅ Usa `secrets` module para seguridad criptográfica

**Antes:**
```python
return f"Unrc2025!{dni}"  # Predecible
```

**Después:**
```python
# Ejemplo de password generada: "aB3!xY9@mK2#pL5%"
# Completamente aleatoria y segura
```

---

### 2. Almacenamiento de Credenciales

**Archivo:** `src/alumnos/services/teams_service.py:388-391`

- ✅ La password se guarda en `Alumno.teams_password`
- ✅ Se guarda al crear usuario nuevo
- ✅ **NUEVO:** Se actualiza al resetear password

**Código agregado:**
```python
# Guardar nueva password en el modelo Alumno
if alumno:
    alumno.teams_password = new_password
    alumno.save(update_fields=['teams_password'])
```

---

### 3. Envío de Credenciales en Email

**Archivo:** `src/alumnos/services/email_service.py:295-420`

#### 3.1 Variable `{password}` disponible en plantillas

Ahora las plantillas personalizadas pueden usar:
- `{nombre}` - Nombre del alumno
- `{apellido}` - Apellido del alumno
- `{upn}` - Email institucional (usuario)
- `{password}` - ⭐ **NUEVO:** Contraseña generada
- `{moodle_url}` - URL del campus virtual
- `{cursos_html}` - Lista de cursos en HTML
- `{cursos_texto}` - Lista de cursos en texto plano

#### 3.2 Email HTML Profesional (Fallback)

Si no hay plantilla personalizada, se envía un email HTML profesional con:
- ✅ Diseño responsive y moderno
- ✅ Credenciales destacadas en recuadro azul
- ✅ Advertencias importantes en recuadro amarillo
- ✅ **Lista de cursos en HTML** (`<ul><li>`)
- ✅ Estilos CSS inline para compatibilidad

**Vista previa:**
```html
🔑 CREDENCIALES DE ACCESO
Usuario: a12345678@eco.unrc.edu.ar
Contraseña: aB3!xY9@mK2#pL5%

📚 CURSOS ENROLLADOS
• Curso 1
• Curso 2
• Curso 3
```

---

### 4. URL Encoding en Teams Service

**Archivo:** `src/alumnos/services/teams_service.py:13,365,330,452`

- ✅ Agregado `from urllib.parse import quote`
- ✅ URLs encode UPN en métodos:
  - `get_user()` - línea 330
  - `reset_password()` - línea 365
  - `delete_user()` - línea 452

**Por qué es importante:**
El símbolo `@` en el UPN debe codificarse como `%40` en las URLs de Microsoft Graph API.

---

## 🔑 Permisos de Azure AD Requeridos

### Permiso CRÍTICO Descubierto

Para resetear passwords se requiere:

✅ **`User.PasswordProfile.ReadWrite.All`** (Application permission)

También conocido como: `User-PasswordProfile.ReadWrite.All` (con guión)

### Checklist Completo de Permisos

**API Permissions (Application):**
- [x] User.ReadWrite.All
- [x] UserAuthenticationMethod.ReadWrite.All
- [x] User.PasswordProfile.ReadWrite.All ⭐ **CRÍTICO**
- [x] Directory.ReadWrite.All
- [x] Group.ReadWrite.All
- [x] Mail.Send
- [x] Admin consent granted ✅

**Directory Role:**
- [x] Password Administrator (o User Administrator) asignado a la Service Principal

---

## 🛠️ Scripts de Utilidad Creados

### 1. `actualizar_plantillas.sh`

Actualiza las plantillas de email en la base de datos con las nuevas versiones.

```bash
chmod +x actualizar_plantillas.sh
./actualizar_plantillas.sh
```

### 2. `check_permissions.py`

Verifica qué permisos tiene el token OAuth2 de Azure AD.

```bash
python check_permissions.py
```

**Output esperado:**
```
✅ TODOS LOS PERMISOS REQUERIDOS ESTÁN PRESENTES
```

### 3. `test_reset_jq.sh`

Prueba el reset de password directamente con Microsoft Graph API.

```bash
./test_reset_jq.sh
```

**Output esperado:**
```
HTTP/2 204  ✅
```

---

## 📚 Documentación Creada

### 1. `PERMISOS_AZURE_AD.md`

Guía completa de configuración de permisos en Azure AD para PyLucy.

Incluye:
- Listado de permisos requeridos
- Instrucciones paso a paso
- Troubleshooting
- Referencias a documentación de Microsoft

### 2. `RESUMEN_ACTUALIZACION.md` (este archivo)

Resumen ejecutivo de todos los cambios implementados.

---

## 🚀 Pasos para Desplegar en Producción

### 1. Actualizar código

```bash
git pull origin main
```

### 2. Reiniciar servicios

```bash
docker compose restart web celery celery-beat
```

### 3. Actualizar plantillas de email

```bash
./actualizar_plantillas.sh
```

### 4. Verificar permisos

```bash
python check_permissions.py
```

Debe mostrar:
```
✅ TODOS LOS PERMISOS REQUERIDOS ESTÁN PRESENTES
```

### 5. Probar reset de password (opcional)

```bash
./test_reset_jq.sh
```

Debe retornar `HTTP/2 204`.

---

## 🧪 Testing

### Probar envío de email con credenciales

1. Ir al admin de Django
2. Seleccionar un alumno de prueba
3. Ejecutar acción "📧 Enrollar en Moodle (envía email)"
4. Verificar que el email contenga:
   - ✅ Usuario (UPN)
   - ✅ Contraseña generada
   - ✅ Lista de cursos en HTML

### Probar reset de password

1. Ir al admin de Django
2. Seleccionar un alumno con cuenta en Teams
3. Ejecutar acción "🔄 Resetear password en Teams"
4. Verificar que:
   - ✅ Password se actualiza en Azure AD
   - ✅ Password se guarda en BD (`teams_password`)
   - ✅ No hay errores 403

---

## 🙏 Agradecimientos

Gracias por descubrir que faltaba el permiso `User.PasswordProfile.ReadWrite.All`. Este hallazgo está documentado en `PERMISOS_AZURE_AD.md` para ayudar a futuros desarrolladores.

---

## 📞 Soporte

Si encuentras algún problema:

1. Verifica los logs: `docker compose logs -f web`
2. Verifica permisos: `python check_permissions.py`
3. Consulta la documentación: `PERMISOS_AZURE_AD.md`

---

**Fin del resumen de actualización**
