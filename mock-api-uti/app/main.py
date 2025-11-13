"""
SIAL UTI Mock V2
----------------
Simulador de endpoints de la API SIAL-UNRC para entornos de prueba.
Genera datos aleatorios (sin base de datos), simulando las listas
de preinscriptos, aspirantes e ingresantes, y los datos personales
de alumnos.

Autor: Proyecto Sistemas Informáticos (UNRC)
Versión: 2.0
"""

import os
import random
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi.middleware.cors import CORSMiddleware


# ---------------------------------------------------------
# Configuración base de la aplicación FastAPI
# ---------------------------------------------------------
app = FastAPI(
    title="SIAL UTI Mock V2",
    version="2.0",
    description="Simulador de endpoints SIAL-UNRC para pruebas locales (sin base de datos)."
)

# ---------------------------------------------------------
# 1️⃣ Middleware CORS (para permitir llamadas desde frontends)
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Permite todos los orígenes (ideal para pruebas locales)
    allow_methods=["*"],      # Permite todos los métodos HTTP
    allow_headers=["*"],      # Permite todos los headers
)

# ---------------------------------------------------------
# 2️⃣ Middleware de semilla (para repetir resultados)
#    Permite usar ?seed=123 en cualquier endpoint
# ---------------------------------------------------------
@app.middleware("http")
async def inject_seed(request: Request, call_next):
    """
    Si la query contiene ?seed=123, fuerza una semilla aleatoria fija.
    Esto permite reproducir los mismos datos en distintas ejecuciones.
    """
    seed = request.query_params.get("seed")
    if seed and seed.isdigit():
        random.seed(int(seed))
    response = await call_next(request)
    return response


# ---------------------------------------------------------
# 3️⃣ Autenticación básica (usuario/contraseña por variable de entorno)
# ---------------------------------------------------------
security = HTTPBasic()

BASIC_USER = os.getenv("BASIC_USER", "usuario")
BASIC_PASS = os.getenv("BASIC_PASS", "contrasena")

# Tipos válidos de listas según la API SIAL
VALID_TIPOS = {"preinscriptos", "aspirantes", "ingresantes"}


def check_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """Verifica usuario y contraseña básica HTTP."""
    is_ok = (credentials.username == BASIC_USER) and (credentials.password == BASIC_PASS)
    if not is_ok:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )


# ---------------------------------------------------------
# 4️⃣ Funciones auxiliares para generar datos aleatorios
# ---------------------------------------------------------

def rand_dni() -> int:
    """Genera un número de DNI aleatorio."""
    return random.randint(10000000, 50000000)


def rand_nombre():
    """
    Genera nombre y apellido aleatorios.
    Cada uno es una cadena de letras A-Z, entre 3 y 12 caracteres.
    """
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def gen(min_len=3, max_len=12):
        n = random.randint(min_len, max_len)
        return "".join(random.choice(letras) for _ in range(n))

    return gen().capitalize(), gen().capitalize()


def rand_mail(nombre: str, apellido: str) -> str:
    """Genera un email a partir del nombre y apellido."""
    dominios = ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "unrc.edu.ar"]
    return f"{nombre.lower()}.{apellido.lower()}@{random.choice(dominios)}"


def rand_tel() -> str:
    """Genera un teléfono aleatorio con prefijo argentino."""
    return f"54-358-{random.randint(400,599)}-{random.randint(1000,9999)}"


def rand_localidad() -> str:
    """Elige una localidad aleatoria (ficticia pero realista)."""
    localidades = ["Río Cuarto", "General Deheza", "Córdoba", "Villa María", "San Luis", "Moldes"]
    return random.choice(localidades)


def rand_fecha_natal() -> str:
    """Genera una fecha de nacimiento entre 1975 y 2005, formato DD/MM/YY."""
    year = random.randint(1975, 2005)
    dt = datetime(year, random.randint(1, 12), random.randint(1, 28))
    return dt.strftime("%d/%m/%y")


def rand_fecha_inscri() -> str:
    """Genera una fecha de inscripción aleatoria entre 2024 y 2025."""
    base = datetime(2024, 1, 1) + timedelta(
        days=random.randint(0, 700),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return base.strftime("%d/%m/%Y %H:%M:%S")


def rand_carrera():
    """Devuelve una carrera aleatoria del catálogo académico."""
    carreras = [
        (1, "INGENIERÍA EN SISTEMAS"),
        (2, "LICENCIATURA EN INFORMÁTICA"),
        (3, "ANALISTA UNIVERSITARIO EN SISTEMAS"),
        (4, "PROFESORADO EN INFORMÁTICA"),
        (5, "INGENIERÍA QUÍMICA"),
    ]
    return random.choice(carreras)


def rand_comisiones(include_inconsistent: bool) -> List[dict]:
    """
    Genera una lista de comisiones (0 a 2 por carrera).
    Si 'include_inconsistent' es True, puede inyectar comisiones con ID 9999999
    para simular inconsistencias (como el catálogo inexistente).
    """
    n = random.randint(0, 2)
    items = []
    for _ in range(n):
        if include_inconsistent and random.random() < 0.25:
            cid = 9999999
            nombre = "Comisión Inconsistente"
        else:
            cid = random.randint(1, 9998)
            nombre = f"Comisión {random.randint(1, 10):02d}"
        items.append({"id_comision": cid, "nombre_comision": nombre})
    return items


def persona_obj(include_inconsistent: bool) -> dict:
    """
    Crea un objeto 'persona' simulando la estructura del servicio SIAL:
    - Documento, carreras, comisiones, cohorte, etc.
    """
    tipodoc = "DNI"
    nrodoc = rand_dni()
    carreras_out = []

    # Cada persona puede tener entre 1 y 2 carreras
    for _ in range(random.randint(1, 2)):
        id_carr, nom_carr = rand_carrera()
        modalidad = random.choice(["1", "2"])  # 1 Presencial, 2 Distancia
        # Cohorte: a veces NULL para probar la regla "cohorte inexistente"
        cohorte = None if random.random() < 0.5 else random.randint(2015, 2025)
        carreras_out.append({
            "id_carrera": id_carr,
            "nombre_carrera": nom_carr,
            "fecha_inscri": rand_fecha_inscri(),
            "modalidad": modalidad,
            "cohorte": cohorte,
            "comisiones": rand_comisiones(include_inconsistent)
        })

    return {
        "tipodoc": tipodoc,
        "nrodoc": nrodoc,
        "carreras": carreras_out
    }


def persons_payload(n: int, include_inconsistent: bool) -> list:
    """Devuelve una lista de 'n' personas simuladas."""
    return [persona_obj(include_inconsistent) for _ in range(n)]


def parse_qty(n: Optional[int]) -> int:
    """
    Determina la cantidad de registros a devolver.
    Si no se especifica 'n', devuelve entre 0 y 5 por defecto.
    """
    if n is None:
        return random.randint(0, 5)
    try:
        n = int(n)
    except Exception:
        n = 0
    return max(0, min(n, 50))


# ---------------------------------------------------------
# 5️⃣ Endpoints principales simulados
# ---------------------------------------------------------

@app.get("/webservice/sial/V2/04/{tipo}/listas/", dependencies=[Depends(check_auth)])
def listas_full(
    tipo: str = Path(..., description="preinscriptos | aspirantes | ingresantes"),
    n: Optional[int] = Query(None, description="Cantidad de registros a simular (0-50). Por defecto aleatorio 0..5"),
    force_inconsistent: bool = Query(False, description="Si true, inyecta comisiones 9999999 aleatoriamente")
):
    """Devuelve la lista completa de personas del tipo indicado."""
    if tipo not in VALID_TIPOS:
        raise HTTPException(status_code=404, detail="Tipo no encontrado")
    qty = parse_qty(n)
    return JSONResponse(content=persons_payload(qty, force_inconsistent))


@app.get("/webservice/sial/V2/04/{tipo}/listas/{fecha}", dependencies=[Depends(check_auth)])
def listas_from_fecha(
    tipo: str,
    fecha: str = Path(..., description="AAAAMMDDHHMM"),
    n: Optional[int] = Query(None),
    force_inconsistent: bool = Query(False)
):
    """Devuelve registros desde una fecha/hora específica."""
    _validate_fecha_compact(fecha)
    if tipo not in VALID_TIPOS:
        raise HTTPException(status_code=404, detail="Tipo no encontrado")
    qty = parse_qty(n)
    return JSONResponse(content=persons_payload(qty, force_inconsistent))


@app.get("/webservice/sial/V2/04/{tipo}/listas/{desde}/{hasta}", dependencies=[Depends(check_auth)])
def listas_rango(
    tipo: str,
    desde: str = Path(..., description="AAAAMMDDHHMM"),
    hasta: str = Path(..., description="AAAAMMDDHHMM"),
    n: Optional[int] = Query(None),
    force_inconsistent: bool = Query(False)
):
    """Devuelve registros dentro de un rango de fechas."""
    _validate_fecha_compact(desde)
    _validate_fecha_compact(hasta)
    if tipo not in VALID_TIPOS:
        raise HTTPException(status_code=404, detail="Tipo no encontrado")
    qty = parse_qty(n)
    return JSONResponse(content=persons_payload(qty, force_inconsistent))


@app.get("/webservice/sial/V2/04/alumnos/datospersonales/{nrodoc}", dependencies=[Depends(check_auth)])
def datos_personales(nrodoc: int = Path(..., description="DNI numérico")):
    """Devuelve los datos personales simulados de un alumno."""
    nombre, apellido = rand_nombre()
    data = [{
        "tipodoc": "DNI",
        "nrodoc": str(nrodoc),
        "nombre": nombre,
        "apellido": apellido,
        "email": rand_mail(nombre, apellido),
        "fecha_natal": rand_fecha_natal(),
        "telefono": rand_tel(),
        "localidad": rand_localidad()
    }]
    return JSONResponse(content=data)


@app.get("/healthz")
def healthz():
    """
    Endpoint de salud simple.
    Permite verificar que el servicio está activo.
    """
    return {"status": "ok"}


def _validate_fecha_compact(fecha: str):
    """Valida formato de fecha AAAAMMDD o AAAAMMDDHHMM."""
    if not (len(fecha) in (8, 12) and fecha.isdigit()):
        raise HTTPException(status_code=400, detail="Formato de fecha inválido (use AAAAMMDDHHMM)")
