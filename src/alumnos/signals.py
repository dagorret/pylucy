"""
Signals para manejar eventos automáticos en el modelo Alumno.
"""
import logging
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import Alumno, Log

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
