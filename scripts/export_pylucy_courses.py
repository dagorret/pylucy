#!/usr/bin/env python
"""
Script para exportar cursos configurados en PyLucy a JSON.
Uso:
    python scripts/export_pylucy_courses.py

O dentro del contenedor:
    docker compose -f docker-compose.dev.yml exec web python scripts/export_pylucy_courses.py
"""
import sys
import os
import django
import json

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
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
