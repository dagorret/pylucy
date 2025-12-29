# Filtros Automáticos - Admin de Alumnos

## 📋 Resumen

Se agregaron 3 filtros personalizados en el admin de Alumnos para facilitar la búsqueda y filtrado de registros según el estado de servicios activados (Teams, Moodle, Email).

---

## 🎯 Filtros Disponibles

### 1. Estado Teams
**¿Qué filtra?** Alumnos con/sin cuenta de Microsoft Teams

| Opción | Criterio | Descripción |
|--------|----------|-------------|
| ✅ Con Teams | `email_institucional` tiene valor | Cuenta Teams creada |
| ❌ Sin Teams | `email_institucional` vacío o NULL | Sin cuenta Teams |

### 2. Estado Moodle
**¿Qué filtra?** Alumnos enrollados/no enrollados en Moodle

| Opción | Criterio | Descripción |
|--------|----------|-------------|
| ✅ Con Moodle | `carreras_data` tiene elementos | Enrollado en al menos un curso |
| ❌ Sin Moodle | `carreras_data` vacío o NULL | Sin cursos asignados |

### 3. Estado Email
**¿Qué filtra?** Alumnos con/sin email configurado

| Opción | Criterio | Descripción |
|--------|----------|-------------|
| 📧 Con email personal | `email_personal` tiene valor | Email personal configurado |
| 🏫 Con email institucional | `email_institucional` tiene valor | Email institucional configurado |
| 📬 Con cualquier email | Al menos uno de los dos | Tiene algún email |
| ❌ Sin email | Ambos vacíos o NULL | Sin email de contacto |

---

## 🔀 Combinación de Filtros

Los filtros son **acumulativos** (funcionan con AND lógico):

```
Filtro 1 ∩ Filtro 2 ∩ Filtro 3 ∩ ... = Resultado
```

### Ejemplo Práctico 1: Aspirantes listos para activación completa

**Objetivo:** Encontrar aspirantes que ya tienen Teams pero todavía no están en Moodle

**Filtros:**
```
┌─────────────────────────────┐
│ Estado actual: aspirante    │
│ Estado Teams: Con Teams     │
│ Estado Moodle: Sin Moodle   │
└─────────────────────────────┘
```

**Resultado:** Lista de aspirantes con Teams activado pendientes de enrollar en Moodle

**Acción sugerida:** Seleccionar todos → "Enrollar en Moodle con email"

---

### Ejemplo Práctico 2: Registros incompletos

**Objetivo:** Encontrar alumnos sin ningún servicio activado

**Filtros:**
```
┌─────────────────────────────┐
│ Estado actual: alumno       │
│ Estado Teams: Sin Teams     │
│ Estado Moodle: Sin Moodle   │
└─────────────────────────────┘
```

**Resultado:** Alumnos sin Teams ni Moodle

**Acción sugerida:** Revisar casos, completar datos, activar servicios

---

### Ejemplo Práctico 3: Contactos perdidos

**Objetivo:** Encontrar registros sin forma de contacto

**Filtros:**
```
┌─────────────────────────────┐
│ Estado Email: Sin email     │
└─────────────────────────────┘
```

**Resultado:** Alumnos sin email_personal ni email_institucional

**Acción sugerida:** Completar información de contacto

---

### Ejemplo Práctico 4: Auditoria de ingresantes

**Objetivo:** Verificar que todos los ingresantes 2025 tienen servicios completos

**Filtros:**
```
┌─────────────────────────────┐
│ Estado actual: ingresante   │
│ Cohorte: 2025               │
│ Estado Teams: Con Teams     │
│ Estado Moodle: Con Moodle   │
└─────────────────────────────┘
```

**Resultado:** Ingresantes 2025 con servicios completos activados

**Acción sugerida:** Exportar lista para reporte

---

## 📊 Casos de Uso por Rol

### 👨‍💼 Administrador
```
Objetivo: Monitorear estado general del sistema

Filtros útiles:
- "Sin Teams" → Ver cuántos faltan activar
- "Sin Moodle" → Ver pendientes de enrollamiento
- "Sin email" → Ver registros incompletos

Acciones: Generar reportes, activar servicios masivamente
```

### 👩‍🏫 Secretaría Académica
```
Objetivo: Preparar ingresantes para inicio de cursillo

Filtros útiles:
- Estado: ingresante
- Cohorte: 2025
- Teams: Sin Teams

Acciones: Activar Teams masivo, verificar enrollamiento
```

### 🔧 Soporte Técnico
```
Objetivo: Resolver tickets de acceso

Filtros útiles:
- Email: Con email personal
- Teams: Sin Teams
- (Buscar por DNI/nombre)

Acciones: Activar cuenta específica, resetear password
```

---

## 🎨 Vista del Admin

### Antes (Filtros básicos)
```
FILTRAR
├─ Estado actual
├─ Modalidad actual
├─ Carrera
└─ Cohorte
```

### Después (Con nuevos filtros)
```
FILTRAR
├─ Estado actual
├─ Modalidad actual
├─ Carrera
├─ Cohorte
├─ 🆕 Estado Teams
├─ 🆕 Estado Moodle
└─ 🆕 Estado Email
```

---

## 💡 Tips de Uso

### Búsquedas Comunes

**1. Preinscriptos con email para enviar bienvenida:**
```
Estado: preinscripto
Email: Con email personal
```

**2. Aspirantes sin Teams (para activar):**
```
Estado: aspirante
Teams: Sin Teams
```

**3. Ingresantes con Teams pero sin Moodle:**
```
Estado: ingresante
Teams: Con Teams
Moodle: Sin Moodle
```

**4. Todos con email institucional (alumnos activos):**
```
Email: Con email institucional
```

### Workflow Recomendado

```
1. FILTRAR → Seleccionar criterios
2. REVISAR → Verificar resultados en lista
3. SELECCIONAR → Marcar checkboxes
4. ACCIÓN → Elegir acción masiva del dropdown
5. CONFIRMAR → Ejecutar
6. VERIFICAR → Volver a filtrar para confirmar cambios
```

---

## 🔍 Consultas SQL Equivalentes

Para referencia técnica, aquí las queries SQL que ejecutan los filtros:

### Estado Teams - Con Teams
```sql
SELECT * FROM alumnos_alumno 
WHERE email_institucional IS NOT NULL 
  AND email_institucional != '';
```

### Estado Moodle - Sin Moodle
```sql
SELECT * FROM alumnos_alumno 
WHERE carreras_data IS NULL 
   OR carreras_data = '[]'::jsonb;
```

### Estado Email - Con cualquier email
```sql
SELECT * FROM alumnos_alumno 
WHERE (email_personal IS NOT NULL AND email_personal != '')
   OR (email_institucional IS NOT NULL AND email_institucional != '');
```

---

## 📝 Notas Técnicas

### Implementación
- **Clase base:** `django.contrib.admin.SimpleListFilter`
- **Método principal:** `queryset(self, request, queryset)` 
- **Retorna:** QuerySet filtrado según `self.value()`

### Performance
- Los filtros usan índices de base de datos cuando están disponibles
- Recomendado: Crear índices en `email_institucional` y `email_personal`
- `carreras_data` usa índices GIN (PostgreSQL) para JSONB

### Compatibilidad
- Django 3.2+
- PostgreSQL (para filtros JSONB en carreras_data)
- Funciona con otros backends pero sin índices JSONB

---

**Autor:** Carlos Dagorret  
**Fecha:** 2025-12-29  
**Ubicación:** `alumnos/admin.py` líneas 2858-2946  
**Licencia:** MIT
