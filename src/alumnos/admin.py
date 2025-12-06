from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path

from .models import Alumno
from .services import ingerir_desde_sial


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    change_list_template = "admin/alumnos/alumno/change_list.html"
    list_display = (
        "apellido",
        "nombre",
        "tipo_documento",
        "dni",
        "estado_actual",
        "modalidad_actual",
        "cohorte",
        "fecha_ingreso",
    )
    list_filter = ("estado_actual", "modalidad_actual", "cohorte")
    search_fields = ("apellido", "nombre", "dni", "email_personal", "email_institucional")
    readonly_fields = (
        "created_at",
        "updated_at",
        "fecha_ultima_modificacion",
        "teams_payload",
        "email_payload",
        "moodle_payload",
    )
    ordering = ("apellido", "nombre")

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "ingesta/",
                self.admin_site.admin_view(self.ingesta_view),
                name="alumnos_alumno_ingesta",
            ),
        ]
        return custom + urls

    def ingesta_view(self, request):
        """
        Endpoint interno para disparar ingestas o borrar alumnos desde la UI del admin.
        Usa POST con `action` para diferenciar.
        """
        if request.method != "POST":
            return redirect("..")

        action = request.POST.get("action")
        n = request.POST.get("n") or None
        seed = request.POST.get("seed") or None
        desde = request.POST.get("desde") or None
        hasta = request.POST.get("hasta") or None
        tipo = request.POST.get("tipo") or None

        if action == "truncate":
            deleted, _ = Alumno.objects.all().delete()
            messages.success(request, f"Alumnos borrados: {deleted}")
            return redirect("..")

        if action == "seed_pre":
            tipo = "preinscriptos"
        elif action == "seed_asp":
            tipo = "aspirantes"
        elif action == "consume":
            if not tipo:
                messages.error(request, "Debe indicar un tipo (preinscriptos, aspirantes, ingresantes).")
                return redirect("..")
            if (desde and not hasta) or (hasta and not desde):
                messages.error(request, "Si usa rango, debe completar 'desde' y 'hasta'.")
                return redirect("..")
        else:
            messages.error(request, "Accion no reconocida.")
            return redirect("..")

        try:
            n_int = int(n) if n is not None and n != "" else None
        except ValueError:
            messages.error(request, "Cantidad 'n' invalida.")
            return redirect("..")

        try:
            seed_int = int(seed) if seed is not None and seed != "" else None
        except ValueError:
            messages.error(request, "Seed invalida.")
            return redirect("..")

        created, updated, errors = ingerir_desde_sial(
            tipo=tipo, n=n_int, fecha=None, desde=desde, hasta=hasta, seed=seed_int
        )
        if errors:
            messages.warning(request, f"Errores: {len(errors)}. Primero: {errors[0]}")
        messages.success(request, f"Ingesta {tipo}: creados {created}, actualizados {updated}")
        return redirect("..")
