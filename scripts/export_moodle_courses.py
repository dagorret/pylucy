#!/usr/bin/env python
"""
Script para exportar cursos de Moodle a JSON.
Uso:
    python scripts/export_moodle_courses.py > cursos_moodle.json
"""
import sys
import os
import django
import json

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from alumnos.services.moodle_service import MoodleService


def export_all_courses():
    """Exporta todos los cursos de Moodle a formato JSON."""
    moodle = MoodleService()

    # Llamar a la API para obtener todos los cursos
    params = {}
    result = moodle._call_webservice('core_course_get_courses', params)

    if 'error' in result:
        print(f"Error obteniendo cursos: {result['error']}", file=sys.stderr)
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
