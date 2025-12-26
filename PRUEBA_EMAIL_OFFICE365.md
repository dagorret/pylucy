# 📧 Formulario de Prueba de Email con Office 365

## 🎯 Propósito

Probar el envío de emails a través de **Office 365** desde el ambiente de **testing** sin modificar la configuración actual de **MailHog**.

El formulario permite ingresar credenciales de Office 365 de forma temporal para realizar pruebas, sin necesidad de cambiar las variables de entorno.

---

## 📍 Ubicación

Dashboard del Admin de Django: **http://localhost:8000/admin/**

En la parte superior verás la sección:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 Probar Envío de Email (Office 365)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📝 Campos del Formulario

### ⚙️ Configuración SMTP (Columna Izquierda)

| Campo | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| **SMTP Host** | `smtp.office365.com` | Servidor SMTP de Office 365 |
| **Puerto** | `587` | Puerto para STARTTLS |
| **Usar TLS** | ✅ Activado | STARTTLS requerido para Office 365 |
| **Usuario** | (vacío) | Email completo (ej: `admin@eco.unrc.edu.ar`) |
| **Contraseña** | (vacío) | Password o App Password si usas MFA |

### ✉️ Contenido del Email (Columna Derecha)

| Campo | Descripción |
|-------|-------------|
| **Remitente (From)** | Dirección que aparecerá como remitente |
| **Destinatario (Para)** | Email donde llegará la prueba |
| **Mensaje personalizado** | (Opcional) Texto del email. Si vacío, usa mensaje por defecto |

---

## 🚀 Cómo Usar

### 1. Configurar SMTP

Completa los campos de la izquierda con tus credenciales de Office 365:

```
SMTP Host:     smtp.office365.com
Puerto:        587
✅ Usar TLS
Usuario:       tu-email@eco.unrc.edu.ar
Contraseña:    tu-password-o-app-password
```

### 2. Configurar Email

Completa los campos de la derecha:

```
Remitente:     no-reply@eco.unrc.edu.ar
Destinatario:  tu-email-personal@gmail.com
Mensaje:       Hola, esto es una prueba de PyLucy
```

### 3. Enviar

Click en **"📤 Enviar Email de Prueba con Office 365"**

### 4. Verificar Resultado

- ✅ **Éxito**: Verás mensaje verde con confirmación
- ❌ **Error**: Verás mensaje rojo con detalles del error

---

## 🔐 App Password para Office 365

Si tienes **autenticación multifactor (MFA)** habilitada:

1. Ve a [https://account.microsoft.com/security](https://account.microsoft.com/security)
2. **Security** → **Advanced security options**
3. **App passwords** → **Create a new app password**
4. Copia el password generado (ej: `abcd efgh ijkl mnop`)
5. Úsalo en el campo **"Contraseña / App Password"**

---

## 💡 Ventajas de este Método

✅ **No afecta MailHog**: La configuración de MailHog en `.env` sigue intacta

✅ **Pruebas rápidas**: No necesitas editar archivos o reiniciar servicios

✅ **Sin riesgos**: Las credenciales no se guardan (solo se usan para esa prueba)

✅ **Mensajes personalizados**: Puedes probar con diferentes textos

✅ **Debugging**: Si falla, muestra el error exacto y sugerencias

---

## 🐛 Troubleshooting

### Error: "Error de autenticación"

**Causa**: Usuario o contraseña incorrectos

**Solución**:
- Verifica que el email sea completo (`admin@eco.unrc.edu.ar`)
- Si usas MFA, usa una **App Password**, no tu password normal
- Verifica que la cuenta tenga permisos de envío SMTP

### Error: "Connection timed out"

**Causa**: No se puede conectar al servidor SMTP

**Solución**:
- Verifica que el contenedor Docker tenga acceso a internet
- Prueba desde el host: `telnet smtp.office365.com 587`
- Verifica firewall/proxy

### Error: "Must issue a STARTTLS command first"

**Causa**: TLS no está habilitado

**Solución**:
- Asegúrate de que el checkbox **"Usar TLS"** esté **marcado** ✅

### El email no llega (sin errores)

**Posibles causas**:
1. Email en carpeta de **spam**
2. Remitente bloqueado por el dominio destino
3. Límite de envíos alcanzado (Office 365 limita a 500-1000/día)

---

## 📊 Después de Probar

### Si funciona ✅

Una vez que compruebes que Office 365 funciona correctamente:

1. **Actualizar `.env.prod`** (o el que uses en producción):
   ```bash
   EMAIL_HOST=smtp.office365.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=admin@eco.unrc.edu.ar
   EMAIL_HOST_PASSWORD=tu-app-password
   EMAIL_FROM=no-reply@eco.unrc.edu.ar
   ```

2. **Reiniciar servicios**:
   ```bash
   docker compose -f docker-compose.prod.yml restart web celery
   ```

3. **Verificar** que los emails de producción se envíen correctamente

---

## 🔒 Seguridad

⚠️ **IMPORTANTE**:
- Las credenciales NO se guardan en la base de datos
- Solo se usan para esa prueba específica
- No se muestran en logs (excepto el usuario)
- Se transmiten por HTTPS en producción

**Recomendación**: Usa una **App Password** dedicada para PyLucy, así puedes revocarla fácilmente si es necesario.

---

## 🎬 Ejemplo de Uso

```
1. Ir a /admin/
2. Ver sección "📧 Probar Envío de Email (Office 365)"
3. Completar:
   - SMTP Host: smtp.office365.com
   - Puerto: 587
   - ✅ Usar TLS
   - Usuario: admin@eco.unrc.edu.ar
   - Contraseña: xxxx-xxxx-xxxx-xxxx (App Password)
   - Remitente: no-reply@eco.unrc.edu.ar
   - Destinatario: mi-email@gmail.com
   - Mensaje: "Prueba de PyLucy desde testing"
4. Click "📤 Enviar Email de Prueba con Office 365"
5. ✅ Ver mensaje: "Email enviado exitosamente..."
6. Verificar bandeja de entrada
```

---

## 📚 Ver También

- [CONFIGURACION_EMAIL_OFFICE365.md](CONFIGURACION_EMAIL_OFFICE365.md) - Guía completa de configuración
- [env-office365-example.txt](env-office365-example.txt) - Plantilla de variables de entorno

---

**Última actualización**: 26 de diciembre de 2025
