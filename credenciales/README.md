# Credenciales de PyLucy

**⚠️ IMPORTANTE: Esta carpeta contiene credenciales sensibles y NO debe subirse a Git.**

Esta carpeta contiene las credenciales reales para los servicios externos:
- **UTI/SIAL**: API del sistema de información académica
- **Moodle**: Plataforma de aprendizaje virtual
- **Microsoft Teams**: Integración con Teams/Azure AD

## Estructura de Archivos

```
credenciales/
├── README.md                    # Este archivo
├── uti_credentials.json         # Credenciales de UTI/SIAL (NO SUBIR)
├── moodle_credentials.json      # Credenciales de Moodle (NO SUBIR)
├── teams_credentials.json       # Credenciales de Teams (NO SUBIR)
├── uti_credentials.json.example # Plantilla para UTI
├── moodle_credentials.json.example # Plantilla para Moodle
└── teams_credentials.json.example # Plantilla para Teams
```

## Configuración Inicial

1. Copia los archivos `.example` y quita el `.example`:
   ```bash
   cd credenciales/
   cp uti_credentials.json.example uti_credentials.json
   cp moodle_credentials.json.example moodle_credentials.json
   cp teams_credentials.json.example teams_credentials.json
   ```

2. Edita cada archivo JSON con las credenciales reales proporcionadas por los administradores de cada servicio.

3. **NUNCA** subas los archivos sin `.example` a Git. La carpeta `credenciales/` (excepto README.md y archivos .example) está en `.gitignore`.

## Seguridad

- ✅ Los archivos en esta carpeta están excluidos de Git
- ✅ Los permisos deben ser 600 (solo lectura/escritura para el propietario)
- ✅ En producción, usa variables de entorno o servicios de secretos
- ⚠️ NO compartas estas credenciales por email o chat sin cifrar
- ⚠️ Rota las credenciales si fueron expuestas

## Respaldo

Mantén un respaldo cifrado de estas credenciales en un lugar seguro, separado del repositorio.
