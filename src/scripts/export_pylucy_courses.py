#!/usr/bin/env python
"""
Nombre del Módulo: export_pylucy_courses.py

Descripción:
Script de utilidad: export_pylucy_courses.

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
Script para exportar cursos configurados en PyLucy a JSON.
Uso dentro del contenedor:
    python scripts/export_pylucy_courses.py
"""
import sys
import os
import django
import json

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pylucy.settings')
django.setup()

from alumnos.models import Configuracion


def export_configured_courses():
    """Exporta los cursos configurados en PyLucy a formato JSON."""
    config = Configuracion.load()

    # Obtener configuración de cursos
    courses_config = config.moodle_courses_config or {}

    output = {
        'moodle_base_url': config.moodle_base_url or 'No configurado',
        'courses_by_status': courses_config,
        'summary': {
            'preinscripto': len(courses_config.get('preinscripto', [])),
            'aspirante': len(courses_config.get('aspirante', [])),
            'ingresante': len(courses_config.get('ingresante', []))
        }
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))

    # Mostrar resumen en stderr
    print(f"\n✅ Cursos configurados en PyLucy:", file=sys.stderr)
    print(f"   - Preinscriptos: {output['summary']['preinscripto']} cursos", file=sys.stderr)
    print(f"   - Aspirantes: {output['summary']['aspirante']} cursos", file=sys.stderr)
    print(f"   - Ingresantes: {output['summary']['ingresante']} cursos", file=sys.stderr)

    if not any(output['summary'].values()):
        print(f"\n⚠️  No hay cursos configurados. Configúralos en Admin > Configuración del Sistema", file=sys.stderr)


if __name__ == '__main__':
    export_configured_courses()
