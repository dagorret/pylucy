"""
Nombre del Módulo: 0027_setup_periodic_tasks.py

Descripción:
Migración de base de datos generada por Django.

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

from django.db import migrations


def crear_tareas_periodicas(apps, schema_editor):
    """
    Crea las tareas periódicas necesarias para el sistema de colas.
    """
    try:
        # Importar modelos de django-celery-beat
        CrontabSchedule = apps.get_model('django_celery_beat', 'CrontabSchedule')
        PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    except LookupError:
        # django-celery-beat no está instalado, saltar
        print("⚠️ django-celery-beat no está instalado, saltando creación de tareas periódicas")
        return

    # 1. Crear crontab: cada 5 minutos
    crontab_5min, _ = CrontabSchedule.objects.get_or_create(
        minute='*/5',
        hour='*',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone='America/Argentina/Cordoba'
    )

    # 2. Crear tarea: Procesador de cola de tareas
    PeriodicTask.objects.update_or_create(
        name='Procesador de Cola de Tareas',
        defaults={
            'task': 'alumnos.tasks.procesar_cola_tareas_pendientes',
            'crontab': crontab_5min,
            'enabled': True,
            'description': 'Procesa tareas pendientes en la cola respetando batch_size y rate_limits. '
                          'Se ejecuta cada 5 minutos. Configurable en Admin → Configuración.',
            'expires': None,  # No expira
        }
    )

    # 3. Crear tarea: Ingesta de preinscriptos
    PeriodicTask.objects.update_or_create(
        name='Ingesta Automática de Preinscriptos',
        defaults={
            'task': 'alumnos.tasks.ingestar_preinscriptos',
            'crontab': crontab_5min,
            'enabled': True,
            'description': 'Ingesta automática de preinscriptos desde API UTI/SIAL. '
                          'Verifica horario configurado internamente antes de ejecutar.',
            'expires': None,
        }
    )

    # 4. Crear tarea: Ingesta de aspirantes
    PeriodicTask.objects.update_or_create(
        name='Ingesta Automática de Aspirantes',
        defaults={
            'task': 'alumnos.tasks.ingestar_aspirantes',
            'crontab': crontab_5min,
            'enabled': True,
            'description': 'Ingesta automática de aspirantes desde API UTI/SIAL. '
                          'Verifica horario configurado internamente antes de ejecutar.',
            'expires': None,
        }
    )

    # 5. Crear tarea: Ingesta de ingresantes
    PeriodicTask.objects.update_or_create(
        name='Ingesta Automática de Ingresantes',
        defaults={
            'task': 'alumnos.tasks.ingestar_ingresantes',
            'crontab': crontab_5min,
            'enabled': True,
            'description': 'Ingesta automática de ingresantes desde API UTI/SIAL. '
                          'Verifica horario configurado internamente antes de ejecutar.',
            'expires': None,
        }
    )

    # 6. Configurar limpieza automática de Celery (si existe)
    try:
        # Crear crontab: diario a las 4 AM
        crontab_4am, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='4',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone='America/Argentina/Cordoba'
        )

        # Actualizar descripción de celery.backend_cleanup si existe
        cleanup_task, created = PeriodicTask.objects.get_or_create(
            name='celery.backend_cleanup',
            defaults={
                'task': 'celery.backend_cleanup',
                'crontab': crontab_4am,
                'enabled': True,
                'description': 'Limpieza automática de resultados viejos en Redis. '
                              'Se ejecuta diariamente a las 4 AM para prevenir acumulación '
                              'de datos y mejorar rendimiento.',
                'expires': None,
            }
        )

        # Si ya existía, solo actualizar descripción
        if not created:
            cleanup_task.description = ('Limpieza automática de resultados viejos en Redis. '
                                        'Se ejecuta diariamente a las 4 AM para prevenir acumulación '
                                        'de datos y mejorar rendimiento.')
            cleanup_task.save()

    except Exception as e:
        print(f"⚠️ No se pudo configurar celery.backend_cleanup: {e}")

    print("✅ Tareas periódicas creadas exitosamente")
    print("   - Procesador de Cola de Tareas (cada 5 min)")
    print("   - Ingesta Automática de Preinscriptos (cada 5 min)")
    print("   - Ingesta Automática de Aspirantes (cada 5 min)")
    print("   - Ingesta Automática de Ingresantes (cada 5 min)")
    print("   - Limpieza de Backend Celery (diario 4 AM)")
    print("   Puedes editarlas en Admin → Periodic tasks")


def eliminar_tareas_periodicas(apps, schema_editor):
    """
    Rollback: elimina las tareas periódicas creadas.
    """
    try:
        PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
        CrontabSchedule = apps.get_model('django_celery_beat', 'CrontabSchedule')
    except LookupError:
        return

    # Eliminar tareas
    PeriodicTask.objects.filter(
        name__in=[
            'Procesador de Cola de Tareas',
            'Ingesta Automática de Preinscriptos',
            'Ingesta Automática de Aspirantes',
            'Ingesta Automática de Ingresantes',
        ]
    ).delete()

    # Eliminar crontab si no se usa en otras tareas
    CrontabSchedule.objects.filter(
        minute='*/5',
        hour='*',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
    ).delete()

    print("🗑️ Tareas periódicas eliminadas")


class Migration(migrations.Migration):

    dependencies = [
        ('alumnos', '0026_configuracion_deshabilitar_fallback_email_personal_and_more'),
    ]

    operations = [
        migrations.RunPython(crear_tareas_periodicas, eliminar_tareas_periodicas),
    ]
