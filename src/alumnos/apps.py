from django.apps import AppConfig


class AlumnosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "alumnos"
    verbose_name = "Alumnos"

    def ready(self):
        """Importa signals y tareas de Celery cuando la app está lista."""
        import alumnos.signals  # noqa
        import alumnos.tasks  # noqa - registrar tareas de Celery
        import alumnos.tasks_delete  # noqa - registrar tareas de borrado
