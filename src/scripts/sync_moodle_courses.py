#!/usr/bin/env python
"""
Nombre del Módulo: sync_moodle_courses.py

Descripción:
Script de utilidad: sync_moodle_courses.

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
"""
Script para sincronizar cursos Moodle desde la tabla cursos_cursoingreso
a la configuración del sistema.

Uso dentro del contenedor:
    python scripts/sync_moodle_courses.py
"""
import sys
import os
import django
import json

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pylucy.settings')
django.setup()

from django.db import connection
from alumnos.models import Configuracion


def sync_courses():
    """Sincroniza cursos desde cursos_cursoingreso a Configuracion."""

    # Leer cursos activos de la tabla
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT curso_moodle
            FROM cursos_cursoingreso
            WHERE activo = true
            ORDER BY curso_moodle
        """)
        cursos_activos = [row[0] for row in cursor.fetchall()]

    if not cursos_activos:
        print("⚠️  No hay cursos activos en cursos_cursoingreso", file=sys.stderr)
        print("   Verifica que la tabla tenga datos con activo=true", file=sys.stderr)
        return

    print(f"✅ Encontrados {len(cursos_activos)} cursos activos en cursos_cursoingreso:")
    for curso in cursos_activos:
        print(f"   - {curso}")

    # Actualizar configuración
    config = Configuracion.load()

    # Mantener preinscripto e ingresante si ya existen, actualizar solo aspirante
    old_config = config.moodle_courses_config or {}

    config.moodle_courses_config = {
        'preinscripto': old_config.get('preinscripto', []),
        'aspirante': cursos_activos,  # Sincronizar desde tabla
        'ingresante': old_config.get('ingresante', [])
    }
    config.save()

    print(f"\n✅ Configuración sincronizada:")
    print(json.dumps(config.moodle_courses_config, indent=2, ensure_ascii=False))

    print(f"\n💡 Tip: Este script lee automáticamente de cursos_cursoingreso")
    print(f"   Si agregas/quitas cursos en la tabla, ejecuta este script de nuevo.")


if __name__ == '__main__':
    sync_courses()
