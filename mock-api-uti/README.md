# SIAL UTI Mock V2 (Docker)

Simulador de la API SIAL/UTI V2 para pruebas locales, sin base de datos, con autenticación **HTTP Basic**.

## Levantar

```bash
docker compose up -d --build
```

Por defecto expone: `http://localhost:8088`

Credenciales configurables en `docker-compose.yml`:
- `BASIC_USER` (default: `usuario`)
- `BASIC_PASS` (default: `contrasena`)

## Endpoints simulados

- `GET /webservice/sial/V2/04/{tipo}/listas/`
- `GET /webservice/sial/V2/04/{tipo}/listas/{fecha}`
- `GET /webservice/sial/V2/04/{tipo}/listas/{desde}/{hasta}`
- `GET /webservice/sial/V2/04/alumnos/datospersonales/{nrodoc}`

Donde `{tipo}` ∈ `{preinscriptos, aspirantes, ingresantes}`.

### Parámetros útiles
- `n`: cantidad de personas a devolver (opcional; por defecto 0..5 aleatorio, máx 50)
- `force_inconsistent=true`: inyecta comisiones con `id_comision=9999999` de forma aleatoria para probar inconsistencias

## Ejemplos

```bash
# Lista completa (ingresantes)
curl -u usuario:contrasena   "http://localhost:8088/webservice/sial/V2/04/ingresantes/listas?n=5&force_inconsistent=true"

# Lista desde fecha
curl -u usuario:contrasena   "http://localhost:8088/webservice/sial/V2/04/preinscriptos/listas/202509100000?n=3"

# Lista por rango
curl -u usuario:contrasena   "http://localhost:8088/webservice/sial/V2/04/aspirantes/listas/20250901/20250910?n=2"

# Datos personales
curl -u usuario:contrasena   "http://localhost:8088/webservice/sial/V2/04/alumnos/datospersonales/27896410"
```
