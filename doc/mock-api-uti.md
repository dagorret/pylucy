# Mock API SIAL/UTI V2

Mock liviano (FastAPI) para simular los servicios SIAL/UTI usados como ingesta.

## Como levantarlo
1) Crear la red externa (una sola vez):
```bash
docker network create devnet
```
2) Ejecutar el mock:
```bash
cd mock-api-uti
docker compose up -d --build
```
3) Base URL por defecto: `http://localhost:8088`
   Credenciales HTTP Basic por defecto: `usuario` / `contrasena` (configurables en `mock-api-uti/docker-compose.yml`).

Para apagarlo:
```bash
cd mock-api-uti
docker compose down
```

## Configuracion en pyLucy
- Vars de entorno en los contenedores de `docker-compose.dev.yml` / `docker-compose.prod.yml`:
  - `SIAL_BASE_URL` (en dev ya apunta a `http://host.docker.internal:8088`)
  - `SIAL_BASIC_USER`
  - `SIAL_BASIC_PASS`
- En Django quedan disponibles en `settings.py` como `SIAL_BASE_URL`, `SIAL_BASIC_USER`, `SIAL_BASIC_PASS` para el cliente de ingesta.

### Acceso desde contenedor (dev)
Usar `http://host.docker.internal:8088` como `SIAL_BASE_URL` para alcanzar el puerto 8088 expuesto en el host.

### Acceso desde host
Si corres pyLucy fuera del contenedor, podes usar `http://localhost:8088` como base URL.

## Endpoints simulados
- `GET /webservice/sial/V2/04/{tipo}/listas/`
- `GET /webservice/sial/V2/04/{tipo}/listas/{fecha}`
- `GET /webservice/sial/V2/04/{tipo}/listas/{desde}/{hasta}`
- `GET /webservice/sial/V2/04/alumnos/datospersonales/{nrodoc}`

`{tipo}` esta en `{preinscriptos, aspirantes, ingresantes}`. Autenticacion HTTP Basic requerida.

### Parametros utiles
- `n`: cantidad de personas a devolver (0-50). Default: 0..5 aleatorio.
- `force_inconsistent=true`: agrega comisiones `9999999` aleatoriamente para probar casos inconsistentes.
- `seed=123`: fuerza semilla aleatoria para reproducir resultados.

### Ejemplos rapidos
```bash
curl -u usuario:contrasena "http://localhost:8088/webservice/sial/V2/04/ingresantes/listas?n=3&seed=42"
curl -u usuario:contrasena "http://localhost:8088/webservice/sial/V2/04/preinscriptos/listas/202509100000"
curl -u usuario:contrasena "http://localhost:8088/webservice/sial/V2/04/aspirantes/listas/20250901/20250910?n=2&force_inconsistent=true"
curl -u usuario:contrasena "http://localhost:8088/webservice/sial/V2/04/alumnos/datospersonales/27896410"
```

## Switch a produccion
Cambiar `SIAL_BASE_URL` a `https://sisinfo.unrc.edu.ar` y ajustar credenciales reales. No se requieren cambios de codigo si el cliente usa las vars de entorno.
