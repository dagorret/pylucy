# 📧 Documentación: Campo Email Status

## 🎯 Resumen

Se agregó una nueva columna **Email** con carita (😊/😡) en el admin de Alumnos, similar a las columnas de Teams y Moodle, para indicar si se envió email correctamente al alumno.

---

## ✨ Cambios Realizados

### 1. **Nuevo campo en modelo Alumno**

**Archivo**: `src/alumnos/models.py:46-49`

```python
email_procesado = models.BooleanField(
    default=False,
    help_text="Indica si se envió email de bienvenida/credenciales al alumno exitosamente"
)
```

### 2. **Nueva columna en Django Admin**

**Archivo**: `src/alumnos/admin.py:29`

```python
list_display = (
    "apellido",
    "nombre",
    "tipo_documento",
    "dni",
    "estado_actual",
    "modalidad_actual",
    "carreras_display",
    "cohorte",
    "fecha_ingreso",
    "teams_status",      # 😊/😡
    "moodle_status",     # 😊/😡
    "email_status",      # 😊/😡 ← NUEVO
)
```

**Método agregado** (`src/alumnos/admin.py:716-724`):

```python
def email_status(self, obj):
    """Muestra estado de Email con emoticono."""
    from django.utils.safestring import mark_safe
    if obj.email_procesado:
        return mark_safe('<span style="font-size: 20px;">😊</span>')
    else:
        return mark_safe('<span style="font-size: 20px;">😡</span>')

email_status.short_description = "Email"
```

### 3. **Actualización automática en tareas**

El campo `email_procesado` se marca como `True` automáticamente cuando:

#### **Para Preinscriptos** (`tasks.py:998-1005`)
- Se envía email de bienvenida exitosamente

```python
email_sent = email_svc.send_welcome_email(alumno)
if email_sent:
    alumno.email_procesado = True
    alumno.save(update_fields=['email_procesado'])
```

#### **Para Aspirantes** (`tasks.py:1027-1036`)
- Se envía email con credenciales de Teams exitosamente
- O se envía email de enrollamiento Moodle (si el primero falló)

```python
email_sent = email_svc.send_credentials_email(alumno, teams_result)
if email_sent:
    alumno.email_procesado = True
    alumno.save(update_fields=['email_procesado'])
```

#### **Para Ingresantes** (`tasks.py:1129-1137`)
- Se envía email de enrollamiento Moodle exitosamente

```python
email_sent = email_svc.send_enrollment_email(alumno, courses_enrolled)
if email_sent:
    alumno.email_procesado = True
    alumno.save(update_fields=['email_procesado'])
```

---

## 📊 Vista en Django Admin

Ahora en `http://localhost:8000/admin/alumnos/alumno/` verás:

```
Apellido  | Nombre | DNI      | ... | Teams | Moodle | Email
----------|--------|----------|-----|-------|--------|-------
García    | Juan   | 12345678 | ... |   😊   |   😊    |  😊
Pérez     | María  | 87654321 | ... |   😊   |   😡    |  😡
López     | Pedro  | 11223344 | ... |   😡   |   😡    |  😡
```

**Interpretación**:
- **😊** = Email enviado exitosamente (`email_procesado = True`)
- **😡** = Email no enviado o falló (`email_procesado = False`)

---

## 🔄 Migración Necesaria

Se debe crear y aplicar una migración:

```bash
# Crear migración
docker compose -f docker-compose.testing.yml exec web python manage.py makemigrations alumnos --name add_email_procesado

# Aplicar migración
docker compose -f docker-compose.testing.yml exec web python manage.py migrate
```

**Migración esperada**:
```python
operations = [
    migrations.AddField(
        model_name='alumno',
        name='email_procesado',
        field=models.BooleanField(default=False,
            help_text='Indica si se envió email de bienvenida/credenciales al alumno exitosamente'),
    ),
]
```

---

## 🧪 Testing

### **Verificar campo en BD**

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell
```

```python
from alumnos.models import Alumno

# Ver alumnos con email procesado
alumnos_con_email = Alumno.objects.filter(email_procesado=True)
print(f"Alumnos con email enviado: {alumnos_con_email.count()}")

# Ver primer alumno
alumno = Alumno.objects.first()
print(f"Teams: {alumno.teams_procesado}")
print(f"Moodle: {alumno.moodle_procesado}")
print(f"Email: {alumno.email_procesado}")  # NUEVO
```

### **Simular envío de email**

```python
from alumnos.models import Alumno

alumno = Alumno.objects.get(dni="12345678")
alumno.email_procesado = True
alumno.save(update_fields=['email_procesado'])

# Ahora debería mostrar 😊 en el admin
```

---

## 📋 Resumen de Archivos Modificados

| Archivo | Líneas | Cambio |
|---------|--------|--------|
| `src/alumnos/models.py` | 46-49 | Campo `email_procesado` |
| `src/alumnos/admin.py` | 29 | Agregar a `list_display` |
| `src/alumnos/admin.py` | 716-724 | Método `email_status()` |
| `src/alumnos/tasks.py` | 998-1005 | Workflow Preinscriptos |
| `src/alumnos/tasks.py` | 1027-1036 | Workflow Aspirantes (credenciales) |
| `src/alumnos/tasks.py` | 1074-1084 | Workflow Aspirantes (enrollamiento) |
| `src/alumnos/tasks.py` | 1129-1137 | Workflow Ingresantes |

---

## 🚀 Despliegue

### **En desarrollo local**

```bash
# 1. Crear migración
docker compose -f docker-compose.testing.yml exec web python manage.py makemigrations alumnos

# 2. Aplicar migración
docker compose -f docker-compose.testing.yml exec web python manage.py migrate

# 3. Reiniciar servicios
docker compose -f docker-compose.testing.yml restart web celery celery-beat
```

### **En servidor remoto**

```bash
# 1. Hacer push desde local
git add .
git commit -m "feat: Agregar campo email_procesado con carita en admin"
git push origin main

# 2. En servidor: pull y actualizar
git pull origin main
./update-testing-prod.sh prod
```

---

## ✅ Checklist Post-Despliegue

- [ ] Migración `add_email_procesado` creada
- [ ] Migración aplicada en BD
- [ ] Campo `email_procesado` existe en tabla `alumnos_alumno`
- [ ] Columna "Email" visible en Django Admin
- [ ] Carita 😊/😡 se muestra correctamente
- [ ] Se marca `email_procesado = True` al enviar emails
- [ ] Workflows de Preinscriptos/Aspirantes/Ingresantes funcionan

---

**Fecha**: 2025-12-17
**Autor**: Carlos + Claude
**Estado**: ✅ Implementado, pendiente de migración
