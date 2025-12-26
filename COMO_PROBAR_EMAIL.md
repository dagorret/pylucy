# 📧 Cómo Probar el Envío de Email con Office 365

## 🎯 Acceso Rápido

1. **Iniciar el ambiente de desarrollo**:
   ```bash
   docker compose up -d
   ```

2. **Ir al Dashboard del Admin**:
   ```
   http://localhost:8000/admin/
   ```

3. **Buscar la sección**:
   ```
   📧 Probar Envío de Email (Office 365 / Graph API)
   ```

---

## 📝 Campos del Formulario

### Remitente (From):
- Debe ser un buzón **válido** en tu Office 365
- Ejemplo: `admin@eco.unrc.edu.ar`
- Este buzón debe existir en tu tenant de Office 365

### Destinatario (Para):
- Cualquier email válido donde quieras recibir la prueba
- Puede ser interno (Office 365) o externo (Gmail, etc.)
- Ejemplo: `tu-email@gmail.com`

### Mensaje personalizado (opcional):
- Si lo dejas vacío, se enviará un mensaje por defecto
- Puedes escribir cualquier texto de prueba aquí

---

## 🚀 Cómo Usar

1. **Llenar el formulario**:
   ```
   Remitente:    admin@eco.unrc.edu.ar
   Destinatario: tu-email-personal@gmail.com
   Mensaje:      Hola, esto es una prueba desde PyLucy
   ```

2. **Click en**: `📤 Enviar Email de Prueba`

3. **Esperar resultado**:
   - ✅ **Éxito**: Mensaje verde confirmando el envío
   - ❌ **Error**: Mensaje rojo con detalles del problema

4. **Verificar bandeja de entrada** del destinatario

---

## 🔧 Detalles Técnicos

### ¿Cómo funciona?

- **Usa Microsoft Graph API**, no SMTP
- **Endpoint**: `https://graph.microsoft.com/v1.0/users/{email_from}/sendMail`
- **Autenticación**: OAuth2 Client Credentials Flow (mismo token que Teams)
- **Permiso requerido**: `Mail.Send` (ya configurado en tu Azure AD)

### Variables de entorno necesarias

Ya están configuradas en tu `.env.dev`:
```bash
TEAMS_TENANT=your-tenant-id
TEAMS_CLIENT_ID=your-client-id
TEAMS_CLIENT_SECRET=your-client-secret
```

**No necesitas** configurar `EMAIL_HOST`, `EMAIL_PORT`, etc. para esta prueba.

---

## ❓ Troubleshooting

### ❌ Error 403: Forbidden

**Posible causa**: Falta permiso `Mail.Send` o no tiene admin consent

**Solución**:
1. Ir a Azure Portal → App Registrations → Tu app
2. API Permissions → Add permission
3. Microsoft Graph → Application permissions → Mail.Send
4. Grant admin consent

### ❌ Error 404: Not Found

**Posible causa**: El buzón remitente no existe en Office 365

**Solución**:
- Verificar que `admin@eco.unrc.edu.ar` (o el email que uses) exista en tu Office 365
- Usar un buzón válido de tu tenant

### ❌ Error de autenticación

**Posible causa**: Credenciales de Azure AD incorrectas en `.env.dev`

**Solución**:
- Verificar `TEAMS_TENANT`, `TEAMS_CLIENT_ID`, `TEAMS_CLIENT_SECRET`
- Asegurarse de que coincidan con tu app en Azure Portal

### ✅ Email no llega (pero no hay error)

**Posibles causas**:
1. Email en carpeta de **spam** → Revisar spam
2. Retraso en entrega → Esperar unos minutos
3. Filtros del servidor destino → Verificar logs

---

## 📊 Verificar Logs

Si algo falla, puedes ver los logs:

```bash
# Ver logs del contenedor web
docker compose logs -f web | grep -i email

# Ver logs de Celery (si usas tareas asíncronas)
docker compose logs -f celery | grep -i email
```

---

## 🎯 Siguiente Paso

Una vez que **confirmes que funciona**:

1. Puedes configurar el sistema para usar Graph API en producción
2. O seguir usando MailHog para desarrollo y Office 365 solo para producción

**MailHog sigue activo** en desarrollo, esta prueba no lo afecta.

---

## 📚 Ver También

- [PRUEBA_EMAIL_OFFICE365.md](PRUEBA_EMAIL_OFFICE365.md) - Documentación detallada anterior
- [CONFIGURACION_EMAIL_OFFICE365.md](CONFIGURACION_EMAIL_OFFICE365.md) - Configuración completa
- [env-office365-example.txt](env-office365-example.txt) - Plantilla de variables

---

**Última actualización**: 25 de diciembre de 2025
