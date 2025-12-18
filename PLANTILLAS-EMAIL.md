# Plantillas de Email - PyLucy

## Descripción

PyLucy ahora soporta plantillas de email personalizables con asuntos dinámicos. Puedes pegar HTML completo y usar variables de reemplazo.

## Cambios Implementados

### 1. Nuevos Campos en el Modelo

Se agregaron los siguientes campos al modelo `Configuracion`:

- `email_asunto_bienvenida` - Asunto del email de bienvenida
- `email_asunto_credenciales` - Asunto del email de credenciales
- `email_asunto_password` - Asunto del email de reseteo de password
- `email_asunto_enrollamiento` - Asunto del email de enrollamiento Moodle
- `email_plantilla_enrollamiento` - Plantilla HTML para enrollamiento

### 2. Variables Disponibles

Cada tipo de email soporta diferentes variables:

#### Email de Bienvenida
- `{nombre}` - Nombre del alumno
- `{apellido}` - Apellido del alumno
- `{dni}` - DNI del alumno
- `{email}` - Email del alumno

#### Email de Credenciales
- `{nombre}` - Nombre del alumno
- `{apellido}` - Apellido del alumno
- `{upn}` - UPN (usuario de Teams)
- `{password}` - Contraseña generada

#### Email de Password
- `{nombre}` - Nombre del alumno
- `{apellido}` - Apellido del alumno
- `{upn}` - UPN (usuario de Teams)
- `{password}` - Nueva contraseña

#### Email de Enrollamiento
- `{nombre}` - Nombre del alumno
- `{apellido}` - Apellido del alumno
- `{upn}` - UPN (usuario de Teams)
- `{moodle_url}` - URL de Moodle
- `{cursos_html}` - Lista de cursos en HTML (`<ul><li>...</li></ul>`)
- `{cursos_texto}` - Lista de cursos en texto plano

### 3. Escape de Llaves en CSS

**IMPORTANTE**: Al pegar HTML con CSS, debes **duplicar las llaves** para que Python no las interprete como variables:

```html
<!-- ❌ INCORRECTO -->
<style>
    body { font-family: Arial; }
</style>

<!-- ✅ CORRECTO -->
<style>
    body {{ font-family: Arial; }}
</style>
```

## Uso

### Opción 1: Cargar Plantillas por Defecto (Recomendado)

Ejecuta el management command para cargar las plantillas HTML por defecto:

```bash
# Desde el contenedor Docker
docker exec pylucy-web python manage.py cargar_plantillas_email

# Sobrescribir plantillas existentes
docker exec pylucy-web python manage.py cargar_plantillas_email --force

# Desde el servidor (sin Docker)
cd src
python manage.py cargar_plantillas_email
```

### Opción 2: Pegar HTML Personalizado

1. Ve al Admin de Django: `/admin/`
2. Navega a **Configuración del Sistema**
3. Expande la sección **✉️ Plantillas de Emails**
4. Pega tu HTML en los campos correspondientes
5. **IMPORTANTE**: Asegúrate de duplicar las llaves `{{ }}` en el CSS

### Opción 3: Exportar/Importar desde Testing

Para copiar las plantillas desde el servidor de testing a producción:

```bash
# Exportar desde testing
docker exec pylucy-web python manage.py dumpdata alumnos.Configuracion --indent 2 > configuracion_backup.json

# Importar en producción
docker exec -i pylucy-web python manage.py loaddata configuracion_backup.json
```

## Migración

La migración `0023_add_email_subjects_and_enrollment.py` se ejecuta automáticamente con:

```bash
docker exec pylucy-web python manage.py migrate
```

## Estructura de Archivos Creados/Modificados

```
pylucy/
├── src/alumnos/
│   ├── models.py                                  # ✅ Modificado: campos de asunto y enrollamiento
│   ├── admin.py                                   # ✅ Modificado: fieldset de plantillas
│   ├── services/email_service.py                  # ✅ Modificado: asuntos dinámicos
│   ├── migrations/
│   │   └── 0023_add_email_subjects_and_enrollment.py  # ✅ Nuevo
│   └── management/commands/
│       └── cargar_plantillas_email.py            # ✅ Nuevo
├── datos-por-defecto.sh                           # ✅ Nuevo (bash script)
└── PLANTILLAS-EMAIL.md                            # ✅ Este archivo
```

## Ejemplos de Plantillas

Las plantillas por defecto incluyen:

1. **Email de Bienvenida**: Simple, con header y footer de la UNRC
2. **Email de Credenciales**: Con credenciales destacadas y botón de acceso a Teams
3. **Email de Password**: Aviso de reseteo con advertencias de seguridad
4. **Email de Enrollamiento**: Acceso al Ecosistema Virtual con lista de cursos

Todas las plantillas usan:
- Diseño responsive (max-width: 600px)
- Colores institucionales (#003366)
- Secciones destacadas con bordes de colores
- Footer con información de la universidad

## Troubleshooting

### Error: `KeyError` al enviar email

Verifica que todas las variables usadas en la plantilla existen en el contexto.

### Email se ve mal (sin estilos)

Algunos clientes de email bloquean CSS. Las plantillas por defecto usan CSS inline y estilos básicos compatibles.

### No se aplican los cambios

1. Guarda la configuración en el admin
2. Verifica que los workers de Celery se reiniciaron
3. Revisa los logs: `docker logs pylucy-worker`

## Roadmap Futuro

- [ ] Agregar preview de emails en el admin
- [ ] Soporte para adjuntos
- [ ] Templates con bloques Jinja2
- [ ] Editor WYSIWYG para plantillas
