from django import forms
from django.contrib import admin

from .constants import CARRERAS_CHOICES
from .models import CursoIngreso, CursoRaro, _normalizar_carreras
from .widgets import CarrerasTagWidget


class BaseCursoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "curso_moodle", "codigo_uti", "carreras_display", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "curso_moodle", "codigo_uti", "carreras")
    ordering = ("nombre",)
    readonly_fields = ()

    def carreras_display(self, obj):
        return ", ".join(obj.carreras)

    carreras_display.short_description = "Carreras"

    def save_model(self, request, obj, form, change):
        # Normaliza carreras si viene como texto
        obj.carreras = _normalizar_carreras(obj.carreras)
        super().save_model(request, obj, form, change)


class CursoIngresoForm(forms.ModelForm):
    carreras = forms.MultipleChoiceField(
        choices=CARRERAS_CHOICES,
        widget=CarrerasTagWidget(attrs={"data-placeholder": "Selecciona o escribe carreras"}),
    )

    class Meta:
        model = CursoIngreso
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial["carreras"] = self.instance.carreras

    def clean_carreras(self):
        return _normalizar_carreras(self.cleaned_data.get("carreras"))


class CursoRaroForm(forms.ModelForm):
    carreras = forms.MultipleChoiceField(
        choices=CARRERAS_CHOICES,
        widget=CarrerasTagWidget(attrs={"data-placeholder": "Selecciona o escribe carreras"}),
    )

    class Meta:
        model = CursoRaro
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial["carreras"] = self.instance.carreras

    def clean_carreras(self):
        return _normalizar_carreras(self.cleaned_data.get("carreras"))


@admin.register(CursoIngreso)
class CursoIngresoAdmin(BaseCursoAdmin):
    form = CursoIngresoForm


@admin.register(CursoRaro)
class CursoRaroAdmin(BaseCursoAdmin):
    list_display = ("nombre", "comision", "curso_moodle", "carreras_display", "activo")
    search_fields = ("nombre", "curso_moodle", "comision", "carreras")
    form = CursoRaroForm
