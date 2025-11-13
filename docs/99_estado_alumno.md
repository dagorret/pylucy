#99 – EstadoActual del Alumno

## Campo en el modelo
- `estado_actual` con choices: PRE, ASP, ING, ALU
- Evolución: preinscripto → aspirante → ingresante → alumno

## Lógica de actualización
Función `actualizar_estado_alumno()` avanza solo si el estado nuevo es superior.

## Ingesta
Cada listado de la UTI llama a esta función según corresponda.

## Admin
- `list_display` incluye estado_actual
- Filtro por estado_actual