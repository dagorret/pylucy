"""
Nombre del Módulo: check_environment.py

Descripción:
Comando de gestión de Django: check_environment.

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

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Verifica el modo de ejecución actual (#ETME)'

    def handle(self, *args, **options):
        mode = settings.ENVIRONMENT_MODE
        prefix = settings.ACCOUNT_PREFIX
        moodle = settings.MOODLE_BASE_URL
        teams_tenant = settings.TEAMS_TENANT

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"MODO ACTUAL: {mode.upper()}")
        self.stdout.write(f"{'='*60}")

        # Información de configuración
        self.stdout.write(f"\n📧 Email Configuration:")
        self.stdout.write(f"   Host: {settings.EMAIL_HOST}")
        self.stdout.write(f"   Port: {settings.EMAIL_PORT}")

        self.stdout.write(f"\n👤 Account Prefix:")
        self.stdout.write(f"   Prefix: {prefix}")
        self.stdout.write(f"   Example: {prefix}12345678@eco.unrc.edu.ar")

        self.stdout.write(f"\n🎓 Moodle:")
        self.stdout.write(f"   URL: {moodle}")
        self.stdout.write(f"   Token configured: {'Yes' if settings.MOODLE_WSTOKEN else 'No'}")

        self.stdout.write(f"\n👥 Microsoft Teams:")
        self.stdout.write(f"   Tenant: {teams_tenant}")
        self.stdout.write(f"   Client ID configured: {'Yes' if settings.TEAMS_CLIENT_ID else 'No'}")
        self.stdout.write(f"   Client Secret configured: {'Yes' if settings.TEAMS_CLIENT_SECRET else 'No'}")

        self.stdout.write(f"\n🌐 SIAL/UTI Mock:")
        self.stdout.write(f"   URL: {settings.SIAL_BASE_URL}")

        self.stdout.write(f"\n{'='*60}")

        if mode == "testing":
            self.stdout.write(self.style.WARNING("\n⚠️  MODO TESTING ACTIVO"))
            self.stdout.write(self.style.WARNING("   - Cuentas con prefijo test-"))
            self.stdout.write(self.style.WARNING("   - Moodle Sandbox (se resetea cada hora)"))
            self.stdout.write(self.style.WARNING("   - Usar para desarrollo/testing únicamente"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ MODO PRODUCCIÓN ACTIVO"))
            self.stdout.write(self.style.ERROR("   ⚠️  CUIDADO: Creará cuentas REALES"))
            self.stdout.write(self.style.ERROR("   ⚠️  Verificar credenciales antes de ejecutar"))

        self.stdout.write(f"\n{'='*60}\n")
