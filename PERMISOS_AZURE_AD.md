# Permisos de Azure AD para PyLucy

## ✅ Permisos requeridos para resetear passwords

Para que PyLucy pueda resetear passwords de usuarios en Azure AD/Microsoft Teams, necesitas **3 componentes**:

### 1. Application Permissions (API Permissions)

Estos se configuran en **Azure Portal → App Registrations → API permissions**:

- ✅ `User.ReadWrite.All` (Application)
- ✅ `UserAuthenticationMethod.ReadWrite.All` (Application)
- ✅ `Directory.ReadWrite.All` (Application)
- ✅ `Group.ReadWrite.All` (Application)
- ✅ `Mail.Send` (Application)

**IMPORTANTE:** Deben ser **Application permissions**, NO Delegated permissions.

Después de agregarlos, hacer click en **"Grant admin consent for [Tu organización]"**.

### 2. Directory Role (Rol de Azure AD)

Además de los permisos de API, la **Service Principal** necesita un rol administrativo:

**Azure Portal → Azure Active Directory → Roles and administrators**

Buscar y asignar **UNO** de estos roles a la aplicación "Lucy":

- ✅ **Password Administrator** (Mínimo recomendado)
- ✅ **User Administrator** (Más permisos)
- ✅ **Privileged Authentication Administrator** (Máximo control)

**Pasos:**
1. Click en el rol (ej: "Password Administrator")
2. **Add assignments**
3. Buscar "Lucy" (tu aplicación)
4. **Add**

### 3. Permiso específico para Password Profile

⚠️ **NUEVO DESCUBRIMIENTO:**

Además de los permisos anteriores, se requiere:

- ✅ `User.PasswordProfile.ReadWrite.All` (Application)

**Este permiso es CRÍTICO para modificar el passwordProfile de usuarios.**

Sin este permiso, obtendrás:
```
403 Forbidden
"Authorization_RequestDenied"
"Insufficient privileges to complete the operation."
```

## 📋 Checklist completo

Verifica que tengas TODOS estos elementos:

### API Permissions (Application)
- [ ] User.ReadWrite.All
- [ ] UserAuthenticationMethod.ReadWrite.All
- [ ] User.PasswordProfile.ReadWrite.All ⭐ **IMPORTANTE**
- [ ] Directory.ReadWrite.All
- [ ] Group.ReadWrite.All
- [ ] Mail.Send
- [ ] Admin consent granted ✅

### Directory Role
- [ ] Password Administrator (o User Administrator) asignado a la Service Principal "Lucy"

## 🔍 Verificar permisos

Puedes verificar qué permisos tiene tu token ejecutando:

```bash
./check_permissions.py
```

Debería mostrar:
```
✓ Roles (Application Permissions):
  - User.ReadWrite.All
  - UserAuthenticationMethod.ReadWrite.All
  - User.PasswordProfile.ReadWrite.All  ⭐
  - Directory.ReadWrite.All
  - Group.ReadWrite.All
  - Mail.Send
```

## 🧪 Probar reset de password

Después de agregar todos los permisos y asignar el rol, espera 5-10 minutos para que se propaguen los cambios.

Luego prueba:

```bash
./test_reset_jq.sh
```

Debería retornar:
```
HTTP/2 204  ✅
```

## 📚 Referencias

- [Microsoft Graph API - Update User](https://learn.microsoft.com/en-us/graph/api/user-update)
- [Password Administrator role](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#password-administrator)
- [Application vs Delegated permissions](https://learn.microsoft.com/en-us/graph/auth/auth-concepts#microsoft-graph-permissions)

## 🙏 Créditos

Gracias por reportar que faltaba `User.PasswordProfile.ReadWrite.All` - ¡esto ayudará a otros desarrolladores que enfrenten el mismo problema!
