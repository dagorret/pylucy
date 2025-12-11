from django.apps import AppConfig


class AlumnosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "alumnos"
    verbose_name = "Alumnos"

    def ready(self):
        """Importa signals cuando la app está lista."""
        import alumnos.signals  # noqa
