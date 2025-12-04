from django import forms
from django.contrib import admin

from .constants import CARRERAS_CHOICES, MODALIDADES_CHOICES
from .models import (
    CursoIngreso,
    _normalizar_carreras,
    _normalizar_comisiones,
    _normalizar_modalidades,
)
from .widgets import CarrerasTagWidget


class BaseCursoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "curso_moodle",
        "comisiones_display",
        "carreras_display",
        "modalidades_display",
        "activo",
    )
    list_filter = ("activo",)
    search_fields = ("nombre", "curso_moodle", "carreras", "modalidades", "comisiones")
    ordering = ("nombre",)
    readonly_fields = ()

    def carreras_display(self, obj):
        return ", ".join(obj.carreras)

    carreras_display.short_description = "Carreras"

    def modalidades_display(self, obj):
        label_map = dict(MODALIDADES_CHOICES)
        return ", ".join(label_map.get(mod, mod) for mod in obj.modalidades)

    modalidades_display.short_description = "Modalidades"

    def comisiones_display(self, obj):
        return ", ".join(obj.comisiones)

    comisiones_display.short_description = "Comisiones"

    def save_model(self, request, obj, form, change):
        # Normaliza carreras si viene como texto
        obj.carreras = _normalizar_carreras(obj.carreras)
        obj.modalidades = _normalizar_modalidades(obj.modalidades)
        obj.comisiones = _normalizar_comisiones(obj.comisiones)
        super().save_model(request, obj, form, change)


class TagsField(forms.MultipleChoiceField):
    """Permite valores fuera de las choices para crear tags nuevos."""

    def validate(self, value):
        if self.required and not value:
            raise forms.ValidationError(self.error_messages["required"], code="required")
        # No validamos contra las choices para permitir tags nuevos.


class BaseCursoForm(forms.ModelForm):
    carreras = TagsField(
        choices=CARRERAS_CHOICES,
        widget=CarrerasTagWidget(attrs={"data-placeholder": "Escribe o selecciona carreras"}),
    )
    modalidades = TagsField(
        choices=MODALIDADES_CHOICES,
        widget=CarrerasTagWidget(attrs={"data-placeholder": "Selecciona modalidad (PRES/DIST)"}),
    )
    comisiones = TagsField(
        choices=(),
        widget=CarrerasTagWidget(attrs={"data-placeholder": "Escribe comisiones y presiona Enter"}),
    )

    class Meta:
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bootstrap_tag_field("carreras", CARRERAS_CHOICES, _normalizar_carreras)
        self._bootstrap_tag_field("modalidades", MODALIDADES_CHOICES, _normalizar_modalidades)
        self._bootstrap_tag_field("comisiones", (), _normalizar_comisiones)

    def _bootstrap_tag_field(self, field_name, base_choices, normalizer):
        """Agrega al select los valores actuales aunque no estén en el catálogo base."""
        field = self.fields[field_name]
        base_choices = list(base_choices)
        base_map = {code: label for code, label in base_choices}

        if self.is_bound:
            prefixed_name = self.add_prefix(field_name)
            if hasattr(self.data, "getlist"):
                raw_values = self.data.getlist(prefixed_name)
            else:
                raw_values = self.data.get(prefixed_name, [])
            current_values = normalizer(raw_values)
        else:
            instance_values = getattr(self.instance, field_name, None) if self.instance and self.instance.pk else []
            current_values = instance_values or []
            if current_values:
                self.initial[field_name] = current_values

        extra_choices = [(value, value) for value in current_values if value not in base_map]
        field.choices = base_choices + extra_choices

    def clean_carreras(self):
        return _normalizar_carreras(self.cleaned_data.get("carreras"))

    def clean_modalidades(self):
        return _normalizar_modalidades(self.cleaned_data.get("modalidades"))

    def clean_comisiones(self):
        return _normalizar_comisiones(self.cleaned_data.get("comisiones"))


class CursoIngresoForm(BaseCursoForm):
    class Meta(BaseCursoForm.Meta):
        model = CursoIngreso


@admin.register(CursoIngreso)
class CursoIngresoAdmin(BaseCursoAdmin):
    form = CursoIngresoForm
