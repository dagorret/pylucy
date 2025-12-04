from django.core.exceptions import ValidationError
from django.db import models


def _normalizar_lista(valor):
    """
    Acepta list/tuple de strings o string separada por comas.
    Devuelve lista de valores en mayúsculas sin espacios.
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
        raise ValidationError("Formato inválido. Usa lista o texto separado por comas.")
    return partes


def _normalizar_carreras(valor):
    return _normalizar_lista(valor)


def _normalizar_modalidades(valor):
    return _normalizar_lista(valor)


def _normalizar_comisiones(valor):
    return _normalizar_lista(valor)


class BaseCurso(models.Model):
    nombre = models.CharField(max_length=150)
    curso_moodle = models.CharField(max_length=150, help_text="Shortname del curso en Moodle")
    carreras = models.JSONField(default=list, help_text="Lista de códigos de carrera (ej: CP, LE)")
    modalidades = models.JSONField(default=list, help_text="Lista de modalidades (ej: PRES, DIST)")
    comisiones = models.JSONField(default=list, help_text="Lista de comisiones (ej: 1, 2, 01, 02)")
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ("nombre",)

    def clean(self):
        super().clean()
        carreras = _normalizar_lista(self.carreras)
        modalidades = _normalizar_lista(self.modalidades)
        comisiones = _normalizar_lista(self.comisiones)
        if not carreras:
            raise ValidationError({"carreras": "Debe indicar al menos una carrera."})
        if not modalidades:
            raise ValidationError({"modalidades": "Debe indicar al menos una modalidad."})
        self.carreras = carreras
        self.modalidades = modalidades
        self.comisiones = comisiones


class CursoIngreso(BaseCurso):
    """Curso de ingreso. Se diferencia por carrera + modalidad + comisión (opcional)."""

    class Meta:
        verbose_name = "Curso de ingreso"
        verbose_name_plural = "Cursos de ingreso"

    def __str__(self):
        suffix = f" [{'/'.join(self.comisiones)}]" if self.comisiones else ""
        return f"{self.nombre}{suffix} ({self.curso_moodle})"
