"""
Signals para manejar eventos automáticos en el modelo Alumno.
"""
import logging
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from .models import Alumno, Log, Configuracion

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=Alumno)
def eliminar_cuentas_externas(sender, instance, **kwargs):
    """
    Antes de eliminar un alumno, programa la eliminación asíncrona de sus cuentas
    en Teams y Moodle usando Celery.
    Solo elimina cuentas con prefijo test-* (seguridad).
    """
    from .tasks import eliminar_cuenta_externa

    alumno = instance

    # Solo eliminar si tiene email_institucional configurado
    if not alumno.email_institucional:
        logger.info(f"Alumno {alumno} no tiene email_institucional, no hay cuentas que eliminar")
        return

    upn = alumno.email_institucional

    # Programar eliminación asíncrona
    logger.info(f"Programando eliminación asíncrona de cuenta: {upn}")

    # Llamar a la tarea de Celery (se ejecutará en background)
    eliminar_cuenta_externa.delay(alumno.id, upn)

    logger.info(f"Eliminación de cuenta {upn} programada en cola de Celery")


@receiver(pre_save, sender=Configuracion)
def resetear_timestamps_ingesta(sender, instance, **kwargs):
    """
    Resetea los timestamps de última ingesta cuando se cambian las fechas de inicio/fin
    en la configuración. Esto permite que las ingestas automáticas vuelvan a consultar
    desde el principio cuando el usuario modifica los rangos de fechas.
    """
    if instance.pk:  # Solo si ya existe (update, no create)
        try:
            old_config = Configuracion.objects.get(pk=instance.pk)

            # Verificar si cambió alguna fecha de preinscriptos
            if (old_config.preinscriptos_dia_inicio != instance.preinscriptos_dia_inicio or
                old_config.preinscriptos_dia_fin != instance.preinscriptos_dia_fin):
                instance.ultima_ingesta_preinscriptos = None
                logger.info("🔄 Reseteando ultima_ingesta_preinscriptos (fechas modificadas)")

            # Verificar si cambió alguna fecha de aspirantes
            if (old_config.aspirantes_dia_inicio != instance.aspirantes_dia_inicio or
                old_config.aspirantes_dia_fin != instance.aspirantes_dia_fin):
                instance.ultima_ingesta_aspirantes = None
                logger.info("🔄 Reseteando ultima_ingesta_aspirantes (fechas modificadas)")

            # Verificar si cambió alguna fecha de ingresantes
            if (old_config.ingresantes_dia_inicio != instance.ingresantes_dia_inicio or
                old_config.ingresantes_dia_fin != instance.ingresantes_dia_fin):
                instance.ultima_ingesta_ingresantes = None
                logger.info("🔄 Reseteando ultima_ingesta_ingresantes (fechas modificadas)")

        except Configuracion.DoesNotExist:
            pass  # Primera vez que se guarda
