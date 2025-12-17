# ✉️ Documentación: Control de Envío de Emails

## 🎯 Resumen

Se agregaron checkboxes configurables para controlar el envío de emails tanto en:
1. **Ingesta manual** (desde admin)
2. **Tareas periódicas** (Celery Beat)

---

## ✨ Nuevas Características

### 1. **Campos en Modelo Configuracion**

**Archivo**: `src/alumnos/models.py`

```python
# Preinscriptos
preinscriptos_enviar_email = models.BooleanField(
    default=True,
    help_text="✉️ Enviar email de bienvenida a preinscriptos durante ingesta automática"
)

# Aspirantes
aspirantes_enviar_email = models.BooleanField(
    default=True,
    help_text="✉️ Enviar emails a aspirantes durante ingesta automática (bienvenida + credenciales + enrollamiento)"
)

# Ingresantes
ingresantes_enviar_email = models.BooleanField(
    default=True,
    help_text="✉️ Enviar email de enrollamiento a ingresantes durante ingesta automática"
)
```

### 2. **Visible en Django Admin**

**Archivo**: `src/alumnos/admin.py`

Ahora en `http://localhost:8000/admin/alumnos/configuracion/` verás:

```
📥 Ingesta Automática - Preinscriptos:
  ☑️ Preinscriptos enviar email

📥 Ingesta Automática - Aspirantes:
  ☑️ Aspirantes enviar email

📥 Ingesta Automática - Ingresantes:
  ☑️ Ingresantes enviar email
```

### 3. **Tareas Periódicas Respetan Configuración**

**Archivo**: `src/alumnos/tasks.py`

#### **Preinscriptos** (línea 51-54)
```python
enviar_email = config.preinscriptos_enviar_email
logger.info(f"[Ingesta Auto-Preinscriptos] Enviar email: {enviar_email}")
created, updated, errors, nuevos_ids = ingerir_desde_sial(
    tipo='preinscriptos',
    retornar_nuevos=True,
    enviar_email=enviar_email
)
```

#### **Aspirantes** (línea 179-182)
```python
enviar_email = config.aspirantes_enviar_email
logger.info(f"[Ingesta Auto-Aspirantes] Enviar email: {enviar_email}")
created, updated, errors, nuevos_ids = ingerir_desde_sial(
    tipo='aspirantes',
    retornar_nuevos=True,
    enviar_email=enviar_email
)
```

#### **Ingresantes** (línea 307-310)
```python
enviar_email = config.ingresantes_enviar_email
logger.info(f"[Ingesta Auto-Ingresantes] Enviar email: {enviar_email}")
created, updated, errors, nuevos_ids = ingerir_desde_sial(
    tipo='ingresantes',
    retornar_nuevos=True,
    enviar_email=enviar_email
)
```

### 4. **Ingesta Manual con Checkbox Dinámico**

**Archivo**: `src/pylucy/templates/admin/alumnos/alumno/change_list.html`

El checkbox de email cambia su texto según el tipo seleccionado:

```
Tipo: [preinscriptos ▼]
☑️ 📧 Enviar email de bienvenida

Tipo: [aspirantes ▼]
☑️ 📧 Enviar emails (bienvenida + credenciales + enrollamiento)

Tipo: [ingresantes ▼]
☑️ 📧 Enviar email de enrollamiento Moodle
```

**JavaScript agregado** (líneas 90-108):
```javascript
function updateEmailCheckboxText() {
  const tipo = tipoSelect.value;
  if (tipo === "preinscriptos") {
    emailText.textContent = "📧 Enviar email de bienvenida";
  } else if (tipo === "aspirantes") {
    emailText.textContent = "📧 Enviar emails (bienvenida + credenciales + enrollamiento)";
  } else if (tipo === "ingresantes") {
    emailText.textContent = "📧 Enviar email de enrollamiento Moodle";
  }
}
```

---

## 📊 Comportamiento por Tipo

| Tipo | Email de Bienvenida | Email de Credenciales | Email de Enrollamiento |
|------|-------------------|---------------------|---------------------|
| **Preinscriptos** | ✅ (si checkbox marcado) | ❌ | ❌ |
| **Aspirantes** | ✅ | ✅ | ✅ (si checkbox marcado) |
| **Ingresantes** | ❌ | ❌ | ✅ (si checkbox marcado) |

---

## 🔧 Configuración

### **Opción A: Django Admin**

```
http://localhost:8000/admin/alumnos/configuracion/
```

1. Desplázate a la sección correspondiente
2. Marca/desmarca el checkbox `enviar_email`
3. Guardar

### **Opción B: Django Shell**

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell
```

```python
from alumnos.models import Configuracion

config = Configuracion.load()

# Habilitar emails para todos
config.preinscriptos_enviar_email = True
config.aspirantes_enviar_email = True
config.ingresantes_enviar_email = True
config.save()

# Deshabilitar emails para preinscriptos
config.preinscriptos_enviar_email = False
config.save()
```

**Luego reiniciar Celery Beat**:
```bash
docker compose -f docker-compose.testing.yml restart celery-beat
```

---

## 🧪 Testing

### **Verificar configuración**

```bash
docker compose -f docker-compose.testing.yml exec web python manage.py shell
```

```python
from alumnos.models import Configuracion

config = Configuracion.load()
print(f"Preinscriptos enviar email: {config.preinscriptos_enviar_email}")
print(f"Aspirantes enviar email: {config.aspirantes_enviar_email}")
print(f"Ingresantes enviar email: {config.ingresantes_enviar_email}")
```

**Output esperado**:
```
Preinscriptos enviar email: True
Aspirantes enviar email: True
Ingresantes enviar email: True
```

### **Probar ingesta manual**

1. Ir a: `http://localhost:8000/admin/alumnos/alumno/`
2. En la sección "Herramientas UTI" → "Consumir"
3. Seleccionar tipo: `preinscriptos`
4. Observar que el checkbox dice: "📧 Enviar email de bienvenida"
5. Cambiar tipo a: `aspirantes`
6. Observar que el checkbox dice: "📧 Enviar emails (bienvenida + credenciales + enrollamiento)"

### **Probar tarea periódica**

```bash
# Habilitar ingesta de preinscriptos SIN email
docker compose -f docker-compose.testing.yml exec web python manage.py shell
```

```python
from alumnos.models import Configuracion
from django.utils import timezone

config = Configuracion.load()
config.preinscriptos_dia_inicio = timezone.now()
config.preinscriptos_enviar_email = False  # ← SIN email
config.save()
exit()
```

```bash
# Reiniciar Celery Beat
docker compose -f docker-compose.testing.yml restart celery-beat

# Ver logs
docker compose -f docker-compose.testing.yml logs -f celery-beat
```

Deberías ver en logs:
```
[Ingesta Auto-Preinscriptos] Enviar email: False
```

---

## 📋 Migración Necesaria

```bash
# Crear migración
docker compose -f docker-compose.testing.yml exec web python manage.py makemigrations alumnos --name add_enviar_email_fields

# Aplicar migración
docker compose -f docker-compose.testing.yml exec web python manage.py migrate
```

**Migración esperada**:
```python
operations = [
    migrations.AddField(
        model_name='configuracion',
        name='preinscriptos_enviar_email',
        field=models.BooleanField(default=True,
            help_text='✉️ Enviar email de bienvenida a preinscriptos durante ingesta automática'),
    ),
    migrations.AddField(
        model_name='configuracion',
        name='aspirantes_enviar_email',
        field=models.BooleanField(default=True,
            help_text='✉️ Enviar emails a aspirantes durante ingesta automática (bienvenida + credenciales + enrollamiento)'),
    ),
    migrations.AddField(
        model_name='configuracion',
        name='ingresantes_enviar_email',
        field=models.BooleanField(default=True,
            help_text='✉️ Enviar email de enrollamiento a ingresantes durante ingesta automática'),
    ),
]
```

---

## 📂 Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `src/alumnos/models.py` | 3 campos booleanos nuevos |
| `src/alumnos/admin.py` | Agregados a fieldsets |
| `src/alumnos/tasks.py` | Tareas periódicas leen configuración |
| `src/pylucy/templates/admin/alumnos/alumno/change_list.html` | Checkbox dinámico con JavaScript |
| `src/alumnos/management/commands/config.py` | Soporte en export/import |

---

## ✅ Checklist Post-Implementación

- [ ] Migración `add_enviar_email_fields` creada
- [ ] Migración aplicada en BD
- [ ] 3 campos booleanos existen en tabla `alumnos_configuracion`
- [ ] Checkboxes visibles en Django Admin
- [ ] Texto del checkbox cambia según tipo en ingesta manual
- [ ] Tareas periódicas respetan configuración
- [ ] Logs muestran "Enviar email: True/False"

---

## 💡 Casos de Uso

### **Caso 1: Deshabilitar emails temporalmente**

Durante mantenimiento de servidor SMTP:

```python
config = Configuracion.load()
config.preinscriptos_enviar_email = False
config.aspirantes_enviar_email = False
config.ingresantes_enviar_email = False
config.save()
```

### **Caso 2: Solo emails para aspirantes (con credenciales)**

```python
config = Configuracion.load()
config.preinscriptos_enviar_email = False  # ← Sin email bienvenida
config.aspirantes_enviar_email = True       # ← Con email credenciales
config.ingresantes_enviar_email = False     # ← Sin email
config.save()
```

### **Caso 3: Testing sin enviar emails**

```bash
# Ingesta manual sin email
1. Seleccionar tipo: preinscriptos
2. DESMARCAR checkbox "📧 Enviar email de bienvenida"
3. Click "Consumir"
```

---

**Fecha**: 2025-12-17
**Autor**: Carlos + Claude
**Estado**: ✅ Implementado, pendiente de migración
