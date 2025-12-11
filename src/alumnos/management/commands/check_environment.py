"""
Comando para verificar el modo de ejecución actual (testing vs producción).

Uso:
    python manage.py check_environment
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
