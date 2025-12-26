#!/usr/bin/env python
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
