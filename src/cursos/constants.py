"""
Nombre del Módulo: constants.py

Descripción:
Constantes y mapeos para la aplicación Cursos.
Define códigos de carreras, modalidades y sus mapeos con IDs externos de UTI/SIAL.

Autor: Carlos Dagorret
Fecha de Creación: 2025-12-29
Última Modificación: 2025-12-29

Licencia: MIT
Copyright (c) 2025 Carlos Dagorret

Permisos:
Se concede permiso, de forma gratuita, a cualquier persona que obtenga una copia
de este software y la documentación asociada (el "Software"), para tratar
en el Software sin restricciones, incluyendo, sin limitación, los derechos
de usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar
y/o vender copias del Software, y para permitir a las personas a las que
se les proporciona el Software hacerlo, sujeto a las siguientes condiciones:

El aviso de copyright anterior y este aviso de permiso se incluirán en todas
las copias o partes sustanciales del Software.

EL SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍA DE NINGÚN TIPO, EXPRESA O
IMPLÍCITA, INCLUYENDO PERO NO LIMITADO A LAS GARANTÍAS DE COMERCIABILIDAD,
IDONEIDAD PARA UN PROPÓSITO PARTICULAR Y NO INFRACCIÓN. EN NINGÚN CASO LOS
AUTORES O TITULARES DE LOS DERECHOS DE AUTOR SERÁN RESPONSABLES DE CUALQUIER
RECLAMO, DAÑO U OTRA RESPONSABILIDAD, YA SEA EN UNA ACCIÓN DE CONTRATO,
AGRAVIO O DE OTRO MODO, QUE SURJA DE, FUERA DE O EN CONEXIÓN CON EL SOFTWARE
O EL USO U OTROS TRATOS EN EL SOFTWARE.
"""

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
