from django.core.exceptions import ValidationError
from django.db import models


def _normalizar_carreras(valor):
    """
    Acepta list/tuple de strings o string separada por comas.
    Devuelve lista de códigos en mayúsculas sin espacios.
    """
    if valor is None:
        return []
    if isinstance(valor, str):
        partes = [p.strip().upper() for p in valor.split(",") if p.strip()]
    elif isinstance(valor, (list, tuple)):
        partes = []
        for item in valor:
            if item is None:
                continue
            partes.extend(str(item).strip().upper().split(","))
        partes = [p for p in (s.strip() for s in partes) if p]
    else:
        raise ValidationError("Formato de carreras inválido. Usa lista o texto separado por comas.")
    return partes


class BaseCurso(models.Model):
    nombre = models.CharField(max_length=150)
    curso_moodle = models.CharField(max_length=150, help_text="Shortname del curso en Moodle")
    codigo_uti = models.CharField(max_length=30, help_text="Código UTI", blank=True, default="")
    carreras = models.JSONField(default=list, help_text="Lista de códigos de carrera (ej: CP, LE)")
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ("nombre",)

    def clean(self):
        super().clean()
        carreras = _normalizar_carreras(self.carreras)
        if not carreras:
            raise ValidationError({"carreras": "Debe indicar al menos una carrera."})
        self.carreras = carreras


class CursoIngreso(BaseCurso):
    """Curso normal: comisión no cambia el curso Moodle."""

    class Meta:
        verbose_name = "Curso de ingreso"
        verbose_name_plural = "Cursos de ingreso"

    def __str__(self):
        return f"{self.nombre} ({self.curso_moodle})"


class CursoRaro(BaseCurso):
    """Excepción por comisión."""

    comision = models.CharField(max_length=50, help_text="Comisión que genera excepción (ej: 1, 2, COM-01)")

    class Meta:
        verbose_name = "Curso raro (excepción)"
        verbose_name_plural = "Cursos raros (excepciones)"
        unique_together = ("comision", "curso_moodle")

    def __str__(self):
        return f"{self.nombre} [{self.comision}] ({self.curso_moodle})"
