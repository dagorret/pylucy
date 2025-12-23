# Códigos de Error - PyLucy

## Códigos de Error para Tareas

### Teams (T-xxx)

| Código | Descripción | Solución |
|--------|-------------|----------|
| T-001 | No tiene email configurado | Asignar email_personal o email_institucional al alumno |
| T-002 | Error al obtener token OAuth2 | Verificar credenciales en Configuración (tenant_id, client_id, client_secret) |
| T-003 | Error al crear usuario en Azure AD | Revisar permisos de la aplicación en Azure Portal |
| T-004 | Usuario ya existe en Teams | Normal - el usuario ya fue creado anteriormente |
| T-005 | Error al asignar licencia | Verificar que haya licencias disponibles en el tenant |
| T-006 | Error al resetear contraseña | Verificar permisos de la aplicación |
| T-007 | Usuario no encontrado en Teams | El usuario no existe, debe crearse primero |
| T-008 | Rate limit excedido | Esperar y reintentar. Ajustar rate_limit_teams en Configuración |
| T-009 | Timeout de conexión | Problemas de red o servicio de Microsoft caído |
| T-999 | Intento de borrar cuenta no-test | Por seguridad, solo se pueden eliminar cuentas test-* |

### Moodle (M-xxx)

| Código | Descripción | Solución |
|--------|-------------|----------|
| M-001 | No tiene email institucional | Crear usuario en Teams primero para generar email institucional |
| M-002 | Error de autenticación con Moodle | Verificar moodle_wstoken en Configuración |
| M-003 | Usuario ya existe en Moodle | Normal - el usuario ya fue creado anteriormente |
| M-004 | Error al crear usuario en Moodle | Revisar permisos del webservice token |
| M-005 | Curso no encontrado | Verificar que el curso existe y el ID es correcto |
| M-006 | Error al enrollar en curso | Revisar permisos del webservice token |
| M-007 | Usuario ya enrollado en curso | Normal - el usuario ya está enrollado |
| M-008 | Rol de estudiante no encontrado | Verificar moodle_student_roleid en Configuración |
| M-009 | Rate limit excedido | Esperar y reintentar. Ajustar rate_limit_moodle en Configuración |
| M-010 | Timeout de conexión | Problemas de red o servicio de Moodle caído |
| M-011 | Método de autenticación inválido | Configurar moodle_auth_method (manual/oauth2/oidc) |

### Email (E-xxx)

| Código | Descripción | Solución |
|--------|-------------|----------|
| E-001 | No tiene email personal | Asignar email_personal al alumno |
| E-002 | Error al enviar email | Verificar configuración SMTP (email_host, email_port) |
| E-003 | Plantilla de email no configurada | Configurar plantillas en Configuración |
| E-004 | Error en variables de plantilla | Verificar que la plantilla use {nombre}, {apellido}, etc. |
| E-005 | Servidor SMTP rechazó el email | Verificar credenciales SMTP |
| E-006 | Email bounce/rebote | Email del alumno es inválido o no existe |
| E-007 | Timeout de conexión SMTP | Problemas de red o servidor SMTP caído |

### SIAL/UTI (U-xxx)

| Código | Descripción | Solución |
|--------|-------------|----------|
| U-001 | Error de autenticación | Verificar sial_basic_user y sial_basic_pass |
| U-002 | API no responde | Verificar sial_base_url y conectividad |
| U-003 | Datos inválidos en respuesta | Contactar soporte UTI |
| U-004 | Alumno no encontrado en SIAL | El alumno no existe en el sistema UTI |
| U-005 | Rate limit excedido | Esperar y reintentar. Ajustar rate_limit_uti en Configuración |
| U-006 | Timeout de conexión | Problemas de red o servicio UTI caído |

### General (G-xxx)

| Código | Descripción | Solución |
|--------|-------------|----------|
| G-001 | Error desconocido | Revisar logs detallados en la tabla Log |
| G-002 | Excepción no capturada | Reportar bug con el stacktrace |
| G-003 | Validación de datos falló | Verificar que el alumno tenga todos los datos requeridos |
| G-004 | Operación cancelada por el usuario | Normal - el usuario canceló la operación |
| G-005 | Configuración incompleta | Completar datos en Configuración del Sistema |
| G-006 | Base de datos no disponible | Verificar conexión a PostgreSQL |

## Estados de Tareas

| Estado | Descripción |
|--------|-------------|
| `pending` | Tarea programada pero no iniciada |
| `running` | Tarea en ejecución |
| `completed` | Tarea completada exitosamente |
| `failed` | Tarea falló con error |

## Formato de Logs

### Log de Inicio
```json
{
  "tipo": "INFO",
  "modulo": "admin_action",
  "mensaje": "Iniciando procesamiento: [nombre_accion]",
  "alumno": "Apellido, Nombre (DNI)",
  "usuario": "admin"
}
```

### Log de Fin (Éxito)
```json
{
  "tipo": "SUCCESS",
  "modulo": "admin_action",
  "mensaje": "Procesamiento completado: [nombre_accion]",
  "alumno": "Apellido, Nombre (DNI)",
  "detalles": {
    "duracion_segundos": 2.5,
    "resultado": "Usuario creado exitosamente"
  }
}
```

### Log de Fin (Error)
```json
{
  "tipo": "ERROR",
  "modulo": "admin_action",
  "mensaje": "Error en procesamiento: [nombre_accion]",
  "alumno": "Apellido, Nombre (DNI)",
  "detalles": {
    "codigo_error": "T-003",
    "error": "Error al crear usuario en Azure AD",
    "duracion_segundos": 1.2
  }
}
```
