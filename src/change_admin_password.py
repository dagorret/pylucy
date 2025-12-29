#!/usr/bin/env python
"""
Nombre del Módulo: change_admin_password.py

Descripción:
Script para cambiar contraseña del admin.

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
Script para cambiar la contraseña del usuario admin

Uso:
    python change_admin_password.py

O desde Docker:
    docker compose -f docker-compose.dev.yml exec web python change_admin_password.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pylucy.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Nueva contraseña - MODIFICAR AQUÍ
NEW_PASSWORD = 'Super2025'
USERNAME = 'admin'

# Cambiar contraseña del usuario
try:
    user = User.objects.get(username=USERNAME)
    user.set_password(NEW_PASSWORD)
    user.save()
    print(f"✅ Contraseña cambiada exitosamente para el usuario '{USERNAME}'")
    print(f"   Nueva contraseña: {NEW_PASSWORD}")
except User.DoesNotExist:
    print(f"❌ Error: El usuario '{USERNAME}' no existe")
except Exception as e:
    print(f"❌ Error: {e}")
