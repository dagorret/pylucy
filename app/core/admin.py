from django.contrib import admin
from .models import (
    Modalidad,
    Plan,
    Carrera,
    Materia,
    Comision,
    Alumno,
    Inscripcion,
)


class InscripcionInline(admin.TabularInline):
    """
    Inscripciones en el admin del Alumno.
    Se ven las materias/comisiones en las que está inscripto.
    """
    model = Inscripcion
    extra = 0
    autocomplete_fields = ("materia", "comision")
    readonly_fields = ("fecha_api", "anio", "creado", "modificado")


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = (
        "dni",
        "apellido",
        "nombre",
        "email",
        "localidad",
        "telefono",
        "modalidad",
        "creado",
    )
    search_fields = ("dni", "apellido", "nombre", "email", "localidad")
    list_filter = ("modalidad",)
    ordering = ("apellido", "nombre")
    inlines = [InscripcionInline]


class ComisionInline(admin.TabularInline):
    """
    Comisiones como inline dentro de Materia.
    """
    model = Comision
    extra = 0
    autocomplete_fields = ("modalidad",)


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = (
        "id_materia_uti",
        "nombre",
        "codigo_corto",
        "codigo_uti",
        "codigo_plan",
    )
    search_fields = ("nombre", "codigo_corto", "codigo_uti", "codigo_plan")
    inlines = [ComisionInline]


@admin.register(Modalidad)
class ModalidadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "codigo_uti")
    search_fields = ("nombre", "codigo", "codigo_uti")


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("id_plan_uti", "anio")
    search_fields = ("id_plan_uti", "anio")


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ("nombre", "plan")
    search_fields = ("nombre",)
    list_filter = ("plan",)


@admin.register(Comision)
class ComisionAdmin(admin.ModelAdmin):
    list_display = ("materia", "nombre", "codigo", "codigo_uti", "modalidad")
    search_fields = ("nombre", "codigo", "codigo_uti", "materia__nombre")
    list_filter = ("modalidad", "materia")


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ("alumno", "materia", "comision", "anio", "fecha_api")
    list_filter = ("anio", "materia", "comision", "comision__modalidad")
    search_fields = (
        "alumno__dni",
        "alumno__apellido",
        "alumno__nombre",
        "materia__nombre",
        "comision__nombre",
    )
    autocomplete_fields = ("alumno", "materia", "comision")
    date_hierarchy = "fecha_api"
