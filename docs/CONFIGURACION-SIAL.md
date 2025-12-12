# Configuración SIAL/UTI - Mock vs Real

## 📊 Estado Actual

PyLucy en el servidor de testing está configurado para usar el **API MOCK** de SIAL/UTI, no el servidor real.

## 🔍 Diferencias

### 🧪 MOCK API (Configuración Actual)

**Configuración en `.env.dev`:**

```bash
SIAL_BASE_URL=http://mock-api-uti:8000
SIAL_BASIC_USER=usuario
SIAL_BASIC_PASS=contrasena
```

**Características:**

- ✅ Servicio corriendo en contenedor Docker local
- ✅ Datos de prueba ficticios pero realistas
- ✅ Respuestas rápidas y predecibles
- ✅ No requiere credenciales de producción
- ✅ Funciona sin conexión a servicios externos
- ✅ Ideal para testing y desarrollo
- ❌ Datos NO son reales de preinscriptos

**Endpoints disponibles:**

- `GET http://mock-api-uti:8000/webservice/sial/V2/04/preinscriptos/listas/{desde}/{hasta}`
- `GET http://mock-api-uti:8000/webservice/sial/V2/04/preinscriptos/preinscripto/{nro_tramite}`

**Datos de prueba que devuelve:**

- Preinscriptos con DNI, nombres, emails ficticios
- Carreras de ejemplo
- Fechas de preinscripción simuladas

---

### 🌐 API REAL de SIAL/UTI

**Configuración (NO activa actualmente):**

```bash
SIAL_BASE_URL=https://sial.unrc.edu.ar
SIAL_BASIC_USER=tu_usuario_real
SIAL_BASIC_PASS=tu_contraseña_real
```

**Características:**

- ✅ Datos reales de preinscriptos de UTI
- ✅ Sincronización con sistema productivo
- ✅ Prueba integración real end-to-end
- ❌ Requiere credenciales de producción
- ❌ Más lento (depende de red y servidor UTI)
- ❌ Puede fallar si UTI está caído
- ❌ Afecta contadores/logs en sistema real

**Endpoints reales:**

- `GET https://sial.unrc.edu.ar/webservice/sial/V2/04/preinscriptos/listas/{desde}/{hasta}`
- `GET https://sial.unrc.edu.ar/webservice/sial/V2/04/preinscriptos/preinscripto/{nro_tramite}`

---

## 🔄 Cómo Cambiar de MOCK a REAL

### Opción 1: Editar .env.dev directamente (Temporal)

En el servidor:

```bash
cd /home/motorola/pylucy

# Editar archivo
nano .env.dev

# Cambiar estas líneas:
# SIAL_BASE_URL=http://mock-api-uti:8000
# Por:
# SIAL_BASE_URL=https://sial.unrc.edu.ar

# Y agregar credenciales reales:
# SIAL_BASIC_USER=usuario_real
# SIAL_BASIC_PASS=contraseña_real

# Guardar (Ctrl+O, Enter, Ctrl+X)

# Reiniciar servicios
docker compose -f docker-compose.testing.yml restart web celery celery-beat
```

### Opción 2: Usar archivo de configuración separado (Recomendado)

```bash
cd /home/motorola/pylucy

# Copiar plantilla
cp .env.testing.real .env.testing.real.configured

# Editar y poner credenciales reales
nano .env.testing.real.configured

# Cuando quieras usar API real:
cp .env.testing.real.configured .env.dev

# Reiniciar
docker compose -f docker-compose.testing.yml restart web celery celery-beat
```

### Opción 3: Variable de entorno en docker-compose (Permanente)

Editar `docker-compose.testing.yml`:

```yaml
web:
  environment:
    - SIAL_BASE_URL=https://sial.unrc.edu.ar
    - SIAL_BASIC_USER=usuario_real
    - SIAL_BASIC_PASS=contraseña_real
```

---

## 🧪 Recomendación para Alfa 1

**USAR MOCK** (configuración actual) porque:

1. **Seguridad**: No arriesgas datos reales
2. **Independencia**: No dependes de que UTI esté disponible
3. **Control**: Puedes modificar datos de prueba fácilmente
4. **Velocidad**: Respuestas instantáneas
5. **Testing**: Puedes probar casos edge sin afectar producción

### Cuándo cambiar a API REAL:

- ✅ **Beta testing**: Cuando quieras validar con datos reales
- ✅ **Pre-producción**: Antes de salir a producción
- ✅ **Demostración**: Para mostrar datos reales a stakeholders
- ✅ **Validación**: Para verificar formato exacto de respuestas UTI

---

## 🔐 Obtener Credenciales de API REAL

Si necesitas credenciales para la API real de SIAL/UTI:

1. Contactar al área de Sistemas de UTI/UNRC
2. Solicitar credenciales de acceso al webservice SIAL
3. Especificar que es para:
   - Sistema: PyLucy (Academic Manager System)
   - Propósito: Sincronización de preinscriptos
   - Ambiente: Testing (primero) → Producción (después)

**Datos a solicitar:**

- URL base: `https://sial.unrc.edu.ar`
- Usuario de autenticación HTTP Basic
- Contraseña de autenticación HTTP Basic
- Documentación de endpoints disponibles
- Límites de rate limiting (si existen)

---

## 🧪 Probar Conectividad

### Con MOCK (actual):

```bash
# Desde el servidor
curl -u usuario:contrasena http://localhost:8088/webservice/sial/V2/04/preinscriptos/listas/20251201/20251231
```

### Con API REAL:

```bash
# Desde el servidor (requiere credenciales reales)
curl -u usuario_real:contraseña_real https://sial.unrc.edu.ar/webservice/sial/V2/04/preinscriptos/listas/20251201/20251231
```

---

## 📊 Logs y Monitoreo

### Ver qué API se está usando:

```bash
# Ver configuración actual
docker compose -f docker-compose.testing.yml exec web python manage.py shell -c "
import os
print('SIAL_BASE_URL:', os.getenv('SIAL_BASE_URL'))
print('SIAL_BASIC_USER:', os.getenv('SIAL_BASIC_USER'))
"
```

### Ver requests a SIAL en logs:

```bash
# Logs de web
docker compose -f docker-compose.testing.yml logs -f web | grep -i sial

# Logs de celery
docker compose -f docker-compose.testing.yml logs -f celery | grep -i sial
```

---

## ⚠️ Advertencias

### Al usar API REAL:

1. **Credenciales sensibles**: NO subir a GitHub
2. **Rate limiting**: UTI puede tener límites de requests
3. **Ambiente**: Asegurarse de usar ambiente de testing de UTI (no producción)
4. **Logs**: La API real puede registrar todos tus accesos
5. **Datos reales**: Manejar con responsabilidad información de estudiantes

### Al usar MOCK:

1. **Datos ficticios**: Recordar que NO son preinscriptos reales
2. **Formatos**: Verificar que coincidan con formato real de UTI
3. **Testing limitado**: No prueba casos extremos de la API real
4. **Sincronización**: Actualizar mock si UTI cambia su API

---

## 📝 Resumen

| Aspecto              | MOCK (Actual)              | API REAL                   |
| -------------------- | -------------------------- | -------------------------- |
| **URL**              | `http://mock-api-uti:8000` | `https://sial.unrc.edu.ar` |
| **Credenciales**     | `usuario` / `contrasena`   | Credenciales reales de UTI |
| **Datos**            | Ficticios de prueba        | Reales de preinscriptos    |
| **Velocidad**        | Rápido                     | Depende de red/servidor    |
| **Disponibilidad**   | 100% (local)               | Depende de UTI             |
| **Seguridad**        | Sin riesgo                 | Requiere precauciones      |
| **Recomendado para** | Alfa/Testing               | Beta/Producción            |

**Estado actual en servidor**: ✅ **MOCK API** (seguro para testing alfa)
