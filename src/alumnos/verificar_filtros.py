"""
Script de verificación para comprobar que los filtros están registrados correctamente.
Ejecutar con: python manage.py shell < verificar_filtros.py
"""

# Importar el admin site personalizado
from alumnos.admin import admin_site

# Obtener el ModelAdmin registrado para Alumno
alumno_admin = admin_site._registry.get(__import__('alumnos.models', fromlist=['Alumno']).Alumno)

if alumno_admin:
    print("✅ Alumno está registrado en PyLucyAdminSite")
    print(f"   Clase: {alumno_admin.__class__.__name__}")
    print(f"\n📋 Filtros configurados ({len(alumno_admin.list_filter)}):")
    for i, filtro in enumerate(alumno_admin.list_filter, 1):
        if isinstance(filtro, str):
            print(f"   {i}. {filtro} (campo)")
        else:
            print(f"   {i}. {filtro.__name__} (filtro personalizado)")
    
    # Verificar filtros específicos
    filtros_esperados = ['TeamsStatusFilter', 'MoodleStatusFilter', 'EmailStatusFilter']
    filtros_encontrados = [f.__name__ for f in alumno_admin.list_filter if not isinstance(f, str)]
    
    print(f"\n🔍 Verificación de nuevos filtros:")
    for filtro in filtros_esperados:
        if filtro in filtros_encontrados:
            print(f"   ✅ {filtro} - OK")
        else:
            print(f"   ❌ {filtro} - NO ENCONTRADO")
else:
    print("❌ Alumno NO está registrado en PyLucyAdminSite")
