from django.core.exceptions import ValidationError
from django.db import models


class Carrera(models.Model):
    """
    Modelo para definir las carreras de la facultad.
    Mapea el ID de la UTI con el código interno y nombre completo.
    """
    id_uti = models.IntegerField(
        unique=True,
        help_text="ID de carrera desde API UTI/SIAL (ej: 2, 3, 4, 7, 8)"
    )
    codigo = models.CharField(
        max_length=10,
        unique=True,
        help_text="Código interno de la carrera (ej: LE, CP, LA, TGA, TGE)"
    )
    nombre_completo = models.CharField(
        max_length=255,
        help_text="Nombre completo de la carrera"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Si la carrera está activa para nuevas inscripciones"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"
        ordering = ["nombre_completo"]

    def __str__(self):
        return f"{self.nombre_completo} ({self.codigo})"


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
