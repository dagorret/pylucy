¿Qué queda “fijo” para el futuro?

Todo el comportamiento de red (URLs, auth) está encapsulado en:

settings.py (constantes)

uti_client.py

Toda la lógica de negocio (estado, creación de alumnos) está encapsulada en:

uti_ingesta.py

services.actualizar_estado_alumno

management command sync_uti

Cambios futuros:

Si la UTI cambia de versión (V2 → V3):
→ tocás UTI_API_LISTAS_BASE y UTI_API_DATOS_PERSONALES.

Si cambian credenciales:
→ tocás el .env o las variables del servidor.

Si agregan campos nuevos de persona:
→ tocás solo obtener_o_crear_alumno_desde_datos.
