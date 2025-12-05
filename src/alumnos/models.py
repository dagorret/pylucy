from django.db import models


class Alumno(models.Model):
    """Modelo base para etapas de preinscripto, aspirante, ingresante y alumno."""

    class Estado(models.TextChoices):
        PREINSCRIPTO = "preinscripto", "Preinscripto"
        ASPIRANTE = "aspirante", "Aspirante"
        INGRESANTE = "ingresante", "Ingresante"
        ALUMNO = "alumno", "Alumno"

    tipo_documento = models.CharField(max_length=20)
    dni = models.CharField(max_length=30)
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    email_personal = models.EmailField()
    fecha_nacimiento = models.DateField(null=True, blank=True)
    cohorte = models.PositiveSmallIntegerField(null=True, blank=True)
    localidad = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    email_institucional = models.EmailField(null=True, blank=True)
    estado_actual = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.PREINSCRIPTO
    )
    fecha_ingreso = models.DateField(null=True, blank=True)
    estado_ingreso = models.CharField(max_length=100, null=True, blank=True)
    modalidad_actual = models.CharField(max_length=1, null=True, blank=True)
    teams_password = models.CharField(max_length=255, null=True, blank=True)
    teams_payload = models.JSONField(null=True, blank=True)
    fecha_ultima_modificacion = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tipo_documento", "dni")
        ordering = ("apellido", "nombre")
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.tipo_documento} {self.dni})"
