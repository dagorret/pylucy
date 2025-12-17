"""
Comando para exportar e importar configuración del sistema en formato JSON.
"""
import json
from django.core.management.base import BaseCommand
from alumnos.models import Configuracion


class Command(BaseCommand):
    help = 'Exporta o importa la configuración del sistema en formato JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['export', 'import'],
            help='Acción a realizar: export o import'
        )
        parser.add_argument(
            '--file',
            type=str,
            default='configuracion.json',
            help='Archivo JSON para exportar/importar (default: configuracion.json)'
        )

    def handle(self, *args, **options):
        action = options['action']
        filename = options['file']

        if action == 'export':
            self.export_config(filename)
        elif action == 'import':
            self.import_config(filename)

    def export_config(self, filename):
        """Exporta la configuración a JSON."""
        config = Configuracion.load()

        # Campos a exportar
        data = {
            # Procesamiento y Rate Limiting
            'batch_size': config.batch_size,
            'rate_limit_teams': config.rate_limit_teams,
            'rate_limit_moodle': config.rate_limit_moodle,
            'rate_limit_uti': config.rate_limit_uti,

            # Ingesta automática
            'preinscriptos_dia_inicio': config.preinscriptos_dia_inicio.isoformat() if config.preinscriptos_dia_inicio else None,
            'preinscriptos_dia_fin': config.preinscriptos_dia_fin.isoformat() if config.preinscriptos_dia_fin else None,
            'preinscriptos_frecuencia_segundos': config.preinscriptos_frecuencia_segundos,
            'preinscriptos_enviar_email': config.preinscriptos_enviar_email,
            'aspirantes_dia_inicio': config.aspirantes_dia_inicio.isoformat() if config.aspirantes_dia_inicio else None,
            'aspirantes_dia_fin': config.aspirantes_dia_fin.isoformat() if config.aspirantes_dia_fin else None,
            'aspirantes_frecuencia_segundos': config.aspirantes_frecuencia_segundos,
            'aspirantes_enviar_email': config.aspirantes_enviar_email,
            'ingresantes_dia_inicio': config.ingresantes_dia_inicio.isoformat() if config.ingresantes_dia_inicio else None,
            'ingresantes_dia_fin': config.ingresantes_dia_fin.isoformat() if config.ingresantes_dia_fin else None,
            'ingresantes_frecuencia_segundos': config.ingresantes_frecuencia_segundos,
            'ingresantes_enviar_email': config.ingresantes_enviar_email,

            # Teams/Azure AD
            'teams_tenant_id': config.teams_tenant_id,
            'teams_client_id': config.teams_client_id,
            'teams_client_secret': config.teams_client_secret,
            'account_prefix': config.account_prefix,

            # API SIAL/UTI
            'sial_base_url': config.sial_base_url,
            'sial_basic_user': config.sial_basic_user,
            'sial_basic_pass': config.sial_basic_pass,

            # Moodle
            'moodle_base_url': config.moodle_base_url,
            'moodle_wstoken': config.moodle_wstoken,
            'moodle_email_type': config.moodle_email_type,
            'moodle_student_roleid': config.moodle_student_roleid,
            'moodle_auth_method': config.moodle_auth_method,

            # Plantillas de emails
            'email_plantilla_bienvenida': config.email_plantilla_bienvenida,
            'email_plantilla_credenciales': config.email_plantilla_credenciales,
            'email_plantilla_password': config.email_plantilla_password,

            # Email SMTP
            'email_from': config.email_from,
            'email_host': config.email_host,
            'email_port': config.email_port,
            'email_use_tls': config.email_use_tls,
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f'✅ Configuración exportada a {filename}'))

    def import_config(self, filename):
        """Importa la configuración desde JSON."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'❌ Archivo no encontrado: {filename}'))
            return
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'❌ Error parseando JSON: {e}'))
            return

        config = Configuracion.load()

        # Importar campos
        from datetime import datetime

        # Procesamiento
        config.batch_size = data.get('batch_size', config.batch_size)
        config.rate_limit_teams = data.get('rate_limit_teams', config.rate_limit_teams)
        config.rate_limit_moodle = data.get('rate_limit_moodle', config.rate_limit_moodle)
        config.rate_limit_uti = data.get('rate_limit_uti', config.rate_limit_uti)

        # Ingesta automática
        if data.get('preinscriptos_dia_inicio'):
            config.preinscriptos_dia_inicio = datetime.fromisoformat(data['preinscriptos_dia_inicio'])
        if data.get('preinscriptos_dia_fin'):
            config.preinscriptos_dia_fin = datetime.fromisoformat(data['preinscriptos_dia_fin'])
        config.preinscriptos_frecuencia_segundos = data.get('preinscriptos_frecuencia_segundos', config.preinscriptos_frecuencia_segundos)
        config.preinscriptos_enviar_email = data.get('preinscriptos_enviar_email', config.preinscriptos_enviar_email)

        if data.get('aspirantes_dia_inicio'):
            config.aspirantes_dia_inicio = datetime.fromisoformat(data['aspirantes_dia_inicio'])
        if data.get('aspirantes_dia_fin'):
            config.aspirantes_dia_fin = datetime.fromisoformat(data['aspirantes_dia_fin'])
        config.aspirantes_frecuencia_segundos = data.get('aspirantes_frecuencia_segundos', config.aspirantes_frecuencia_segundos)
        config.aspirantes_enviar_email = data.get('aspirantes_enviar_email', config.aspirantes_enviar_email)

        if data.get('ingresantes_dia_inicio'):
            config.ingresantes_dia_inicio = datetime.fromisoformat(data['ingresantes_dia_inicio'])
        if data.get('ingresantes_dia_fin'):
            config.ingresantes_dia_fin = datetime.fromisoformat(data['ingresantes_dia_fin'])
        config.ingresantes_frecuencia_segundos = data.get('ingresantes_frecuencia_segundos', config.ingresantes_frecuencia_segundos)
        config.ingresantes_enviar_email = data.get('ingresantes_enviar_email', config.ingresantes_enviar_email)

        # Teams
        config.teams_tenant_id = data.get('teams_tenant_id', config.teams_tenant_id)
        config.teams_client_id = data.get('teams_client_id', config.teams_client_id)
        config.teams_client_secret = data.get('teams_client_secret', config.teams_client_secret)
        config.account_prefix = data.get('account_prefix', config.account_prefix)

        # SIAL/UTI
        config.sial_base_url = data.get('sial_base_url', config.sial_base_url)
        config.sial_basic_user = data.get('sial_basic_user', config.sial_basic_user)
        config.sial_basic_pass = data.get('sial_basic_pass', config.sial_basic_pass)

        # Moodle
        config.moodle_base_url = data.get('moodle_base_url', config.moodle_base_url)
        config.moodle_wstoken = data.get('moodle_wstoken', config.moodle_wstoken)
        config.moodle_email_type = data.get('moodle_email_type', config.moodle_email_type)
        config.moodle_student_roleid = data.get('moodle_student_roleid', config.moodle_student_roleid)
        config.moodle_auth_method = data.get('moodle_auth_method', config.moodle_auth_method)

        # Plantillas
        config.email_plantilla_bienvenida = data.get('email_plantilla_bienvenida', config.email_plantilla_bienvenida)
        config.email_plantilla_credenciales = data.get('email_plantilla_credenciales', config.email_plantilla_credenciales)
        config.email_plantilla_password = data.get('email_plantilla_password', config.email_plantilla_password)

        # Email
        config.email_from = data.get('email_from', config.email_from)
        config.email_host = data.get('email_host', config.email_host)
        config.email_port = data.get('email_port', config.email_port)
        config.email_use_tls = data.get('email_use_tls', config.email_use_tls)

        config.save()

        self.stdout.write(self.style.SUCCESS(f'✅ Configuración importada desde {filename}'))
