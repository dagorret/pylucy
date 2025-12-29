#!/usr/bin/env python
"""
Nombre del Módulo: export_moodle_courses.py

Descripción:
Script de utilidad: export_moodle_courses.

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
Script para exportar cursos de Moodle a JSON.
Uso dentro del contenedor:
    python scripts/export_moodle_courses.py > cursos_moodle.json
"""
import sys
import os
import django
import json

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pylucy.settings')
django.setup()

from alumnos.services.moodle_service import MoodleService


def export_all_courses():
    """Exporta todos los cursos de Moodle a formato JSON."""
    moodle = MoodleService()

    # Intentar con diferentes métodos según permisos
    # Método 1: core_course_get_courses (requiere permisos admin)
    params = {}
    result = moodle._call_webservice('core_course_get_courses', params)

    # Si falla por permisos, intentar método alternativo
    if 'error' in result or not isinstance(result, list):
        print(f"⚠️  Método 1 falló: {result.get('error', 'No es lista')}", file=sys.stderr)
        print(f"Intentando método alternativo...", file=sys.stderr)

        # Método 2: Buscar por campo (más permisivo)
        # Buscar todos los cursos visibles
        result = moodle._call_webservice('core_course_search_courses', {
            'criterianame': 'search',
            'criteriavalue': ''
        })

        if 'error' in result:
            print(f"❌ Error obteniendo cursos: {result['error']}", file=sys.stderr)
            print(f"\n💡 Solución: El token de Moodle necesita permisos para:", file=sys.stderr)
            print(f"   - core_course_get_courses, o", file=sys.stderr)
            print(f"   - core_course_search_courses", file=sys.stderr)
            print(f"\nContacta al administrador de Moodle para agregar estos permisos al webservice.", file=sys.stderr)
            sys.exit(1)

        # Extraer cursos del resultado de búsqueda
        if isinstance(result, dict) and 'courses' in result:
            result = result['courses']
        else:
            print(f"Respuesta inesperada: {result}", file=sys.stderr)
            sys.exit(1)

    if not isinstance(result, list):
        print(f"Respuesta inesperada: {result}", file=sys.stderr)
        sys.exit(1)

    # Filtrar y formatear cursos
    courses = []
    for course in result:
        # Saltar el curso "Sitio" (ID 1)
        if course.get('id') == 1:
            continue

        courses.append({
            'id': course.get('id'),
            'shortname': course.get('shortname'),
            'fullname': course.get('fullname'),
            'categoryid': course.get('categoryid'),
            'categoryname': course.get('categoryname', ''),
            'visible': course.get('visible', 1),
            'format': course.get('format', 'topics'),
            'enrollmentmethods': course.get('enrollmentmethods', []),
        })

    # Ordenar por ID
    courses.sort(key=lambda x: x['id'])

    # Exportar a JSON
    output = {
        'total': len(courses),
        'courses': courses,
        'config_format': {
            'preinscripto': [],
            'aspirante': [],
            'ingresante': []
        }
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))

    # Mostrar resumen en stderr
    print(f"\n✅ Exportados {len(courses)} cursos de Moodle", file=sys.stderr)
    print(f"\nEjemplo de configuración para Configuración del Sistema:", file=sys.stderr)
    print(f"(Copia los shortnames que necesites según el estado del alumno)", file=sys.stderr)
    print(f"\nJSON de ejemplo:", file=sys.stderr)
    print(json.dumps(output['config_format'], indent=2), file=sys.stderr)


if __name__ == '__main__':
    export_all_courses()
