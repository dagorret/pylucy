CARRERAS_CHOICES = [
    ("LE", "LE (2)"),
    ("CP", "CP (3)"),
    ("LA", "LA (4)"),
    ("TGA", "TGA (7)"),
    ("TGE", "TGE (8)"),
]

# Diccionario base para mapear IDs externos -> código interno de carrera.
CARRERAS_DICT = {
    "2": "LE",
    "3": "CP",
    "4": "LA",
    "7": "TGA",
    "8": "TGE",
    # soporta enteros también
    2: "LE",
    3: "CP",
    4: "LA",
    7: "TGA",
    8: "TGE",
}

MODALIDADES_CHOICES = [
    ("PRES", "Presencial"),
    ("DIST", "Distancia"),
]

# Mapeo de códigos de modalidad de UTI/SIAL a códigos internos
MODALIDADES_DICT = {
    "1": "PRES",  # Presencial
    "2": "DIST",  # Distancia
    # Soporta enteros también
    1: "PRES",
    2: "DIST",
    # Soporta códigos internos (idempotente)
    "PRES": "PRES",
    "DIST": "DIST",
}
