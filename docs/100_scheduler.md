#100 – Scheduler + Configuración + Cron

## Componentes
- Tabla `UTISyncConfig`
- Tareas A (listados), B (barrido), C (detalles)
- Cron ejecutando cada minuto
- Management command `run_uti_scheduler`
- Lock global para evitar concurrencia

## Flujo general
1. Cron llama scheduler
2. Scheduler mira la tabla
3. Si corresponde, ejecuta A, B o C
4. Respeta el lock global
5. Actualiza next_run_at

## Admin
- Burócrata puede definir días, horas y cantidad de ejecuciones
- Botón manual para A
- Acción para sincronizar un alumno puntual