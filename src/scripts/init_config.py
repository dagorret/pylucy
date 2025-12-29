#!/usr/bin/env python
"""
Nombre del Módulo: init_config.py

Descripción:
Script de utilidad: init_config.

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
Script para inicializar la configuración del sistema en la base de datos.
Se ejecuta automáticamente en el entrypoint para ambientes de testing.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pylucy.settings')
django.setup()

from alumnos.models import Configuracion


def init_testing_config():
    """
    Inicializa la configuración para ambiente de testing.
    Solo se ejecuta si el modo es 'testing' y si los campos están vacíos.
    """
    environment_mode = os.getenv('ENVIRONMENT_MODE', 'testing')

    if environment_mode != 'testing':
        print(f"ℹ️  Modo {environment_mode}: No se inicializa configuración automática")
        return

    # Obtener o crear configuración
    config, created = Configuracion.objects.get_or_create(pk=1)

    updated_fields = []

    # Moodle - solo si están vacíos
    moodle_url = os.getenv('MOODLE_BASE_URL', '')
    moodle_token = os.getenv('MOODLE_WSTOKEN', '')

    if not config.moodle_base_url and moodle_url:
        config.moodle_base_url = moodle_url
        updated_fields.append('moodle_base_url')
        print(f"✅ Moodle URL configurado: {moodle_url}")

    if not config.moodle_wstoken and moodle_token:
        config.moodle_wstoken = moodle_token
        updated_fields.append('moodle_wstoken')
        print(f"✅ Moodle Token configurado: {moodle_token[:20]}...")

    # Teams - solo si están vacíos
    teams_tenant = os.getenv('TEAMS_TENANT', '')
    teams_client_id = os.getenv('TEAMS_CLIENT_ID', '')
    teams_client_secret = os.getenv('TEAMS_CLIENT_SECRET', '')

    if not config.teams_tenant_id and teams_tenant:
        config.teams_tenant_id = teams_tenant
        updated_fields.append('teams_tenant_id')
        print(f"✅ Teams Tenant configurado: {teams_tenant[:20]}...")

    if not config.teams_client_id and teams_client_id:
        config.teams_client_id = teams_client_id
        updated_fields.append('teams_client_id')
        print(f"✅ Teams Client ID configurado: {teams_client_id[:20]}...")

    if not config.teams_client_secret and teams_client_secret:
        config.teams_client_secret = teams_client_secret
        updated_fields.append('teams_client_secret')
        print(f"✅ Teams Client Secret configurado")

    # Account Prefix - solo si está vacío
    account_prefix = os.getenv('ACCOUNT_PREFIX', 'test-a')
    if not config.account_prefix:
        config.account_prefix = account_prefix
        updated_fields.append('account_prefix')
        print(f"✅ Account Prefix configurado: {account_prefix}")

    # Email - solo si están vacíos
    email_host = os.getenv('EMAIL_HOST', 'mailhog')
    email_port = os.getenv('EMAIL_PORT', '1025')
    email_from = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@eco.unrc.edu.ar')

    if not config.email_host:
        config.email_host = email_host
        updated_fields.append('email_host')
        print(f"✅ Email Host configurado: {email_host}")

    if config.email_port is None:
        config.email_port = int(email_port)
        updated_fields.append('email_port')
        print(f"✅ Email Port configurado: {email_port}")

    if not config.email_from:
        config.email_from = email_from
        updated_fields.append('email_from')
        print(f"✅ Email From configurado: {email_from}")

    if config.email_use_tls is None:
        config.email_use_tls = os.getenv('EMAIL_USE_TLS', 'False').lower() == 'true'
        updated_fields.append('email_use_tls')
        print(f"✅ Email Use TLS configurado: {config.email_use_tls}")

    # Guardar si hubo cambios
    if updated_fields:
        config.actualizado_por = 'system:init_config'
        config.save()
        print(f"\n✅ Configuración inicializada con {len(updated_fields)} campos actualizados")
    else:
        if created:
            config.save()
            print("✅ Configuración creada (usando valores por defecto)")
        else:
            print("ℹ️  Configuración ya existe, no se sobrescribe")


if __name__ == '__main__':
    try:
        init_testing_config()
    except Exception as e:
        print(f"❌ Error inicializando configuración: {e}")
        sys.exit(1)
