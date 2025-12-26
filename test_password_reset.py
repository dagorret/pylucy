#!/usr/bin/env python
"""
Script de prueba para resetear password en Teams/Azure AD.
Prueba con URL encoding del UPN.
"""
import os
import sys
import django
from urllib.parse import quote

# Setup Django
sys.path.insert(0, '/home/carlos/work/pylucy/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pylucy.settings')
django.setup()

from alumnos.services.teams_service import TeamsService

def test_reset_password(upn: str):
    """
    Prueba resetear password con URL encoding.
    """
    print(f"\n{'='*60}")
    print(f"PRUEBA: Resetear password para {upn}")
    print(f"{'='*60}\n")

    # Mostrar UPN codificado
    upn_encoded = quote(upn, safe='')
    print(f"UPN original: {upn}")
    print(f"UPN codificado: {upn_encoded}\n")

    # Crear servicio y resetear password
    teams_svc = TeamsService()

    try:
        nueva_password = teams_svc.reset_password(upn)

        if nueva_password:
            print(f"✅ PASSWORD RESETEADA EXITOSAMENTE")
            print(f"Nueva password: {nueva_password}")
            print(f"\nEl usuario deberá cambiar la password en el próximo login.")
            return True
        else:
            print(f"❌ ERROR: No se pudo resetear la password")
            return False

    except Exception as e:
        print(f"❌ EXCEPCIÓN: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    upn = "test-a48325621@eco.unrc.edu.ar"
    success = test_reset_password(upn)

    print(f"\n{'='*60}")
    if success:
        print("RESULTADO: ✅ ÉXITO")
    else:
        print("RESULTADO: ❌ FALLO")
    print(f"{'='*60}\n")

    sys.exit(0 if success else 1)
