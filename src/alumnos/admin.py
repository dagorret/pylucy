from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from django.utils import timezone
from datetime import timedelta

from .models import Alumno, Log, Configuracion, Tarea
from .services import ingerir_desde_sial  # función en services.py (archivo)
from .services.teams_service import TeamsService  # clase en services/ (directorio)
from .services.email_service import EmailService  # clase en services/ (directorio)


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
        "carreras_display",
        "cohorte",
        "fecha_ingreso",
    )
    list_filter = ("estado_actual", "modalidad_actual", "cohorte")
    search_fields = ("apellido", "nombre", "dni", "email_personal", "email_institucional", "carreras_data__nombre_carrera")
    readonly_fields = (
        "created_at",
        "updated_at",
        "fecha_ultima_modificacion",
        "carreras_data",
        "teams_payload",
        "email_payload",
        "moodle_payload",
    )
    ordering = ("apellido", "nombre")
    actions = [
        'activar_teams_email',
        'resetear_y_enviar_email',
        'crear_usuario_teams',
        'resetear_password_teams',
    ]

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

    @admin.action(description="🚀 Activar Teams + Enviar Email con credenciales")
    def activar_teams_email(self, request, queryset):
        """
        Crea usuario en Teams y envía email con credenciales (modo asíncrono).
        Las tareas se ejecutan en background vía Celery.
        """
        from .tasks import activar_servicios_alumno
        from .models import Tarea

        tareas_programadas = 0
        skipped_count = 0

        for alumno in queryset:
            # Validar que tenga email
            if not alumno.email:
                self.message_user(
                    request,
                    f"⚠️ {alumno.apellido}, {alumno.nombre} no tiene email configurado",
                    level=messages.WARNING
                )
                skipped_count += 1
                continue

            # Programar tarea asíncrona
            task = activar_servicios_alumno.delay(alumno.id)

            # Crear registro de tarea
            Tarea.objects.create(
                tipo=Tarea.TipoTarea.ACTIVAR_SERVICIOS,
                estado=Tarea.EstadoTarea.PENDING,
                celery_task_id=task.id,
                alumno=alumno,
                usuario=request.user.username if request.user.is_authenticated else None
            )

            tareas_programadas += 1

        # Resumen final
        self.message_user(
            request,
            f"📋 {tareas_programadas} tareas programadas en cola de Celery. "
            f"Revisa la tabla de Tareas Asíncronas para ver el progreso.",
            level=messages.SUCCESS
        )

        if skipped_count > 0:
            self.message_user(
                request,
                f"⚠️ {skipped_count} alumnos omitidos por falta de email",
                level=messages.WARNING
            )

    @admin.action(description="🔄 Generar contraseña y enviar correo")
    def resetear_y_enviar_email(self, request, queryset):
        """
        Resetea contraseña en Teams y envía email (modo asíncrono).
        Las tareas se ejecutan en background vía Celery.
        """
        from .tasks import resetear_password_y_enviar_email
        from .models import Tarea

        tareas_programadas = 0
        skipped_count = 0

        for alumno in queryset:
            if not alumno.email:
                self.message_user(
                    request,
                    f"⚠️ {alumno.apellido}, {alumno.nombre} no tiene email configurado",
                    level=messages.WARNING
                )
                skipped_count += 1
                continue

            # Programar tarea asíncrona
            task = resetear_password_y_enviar_email.delay(alumno.id)

            # Crear registro de tarea
            Tarea.objects.create(
                tipo=Tarea.TipoTarea.RESETEAR_PASSWORD,
                estado=Tarea.EstadoTarea.PENDING,
                celery_task_id=task.id,
                alumno=alumno,
                usuario=request.user.username if request.user.is_authenticated else None
            )

            tareas_programadas += 1

        # Resumen final
        self.message_user(
            request,
            f"📋 {tareas_programadas} tareas programadas en cola de Celery. "
            f"Revisa la tabla de Tareas Asíncronas para ver el progreso.",
            level=messages.SUCCESS
        )

        if skipped_count > 0:
            self.message_user(
                request,
                f"⚠️ {skipped_count} alumnos omitidos por falta de email",
                level=messages.WARNING
            )

    @admin.action(description="👤 Crear usuario en Teams (sin email)")
    def crear_usuario_teams(self, request, queryset):
        """
        Crea usuario en Teams sin enviar email (modo asíncrono).
        Las tareas se ejecutan en background vía Celery.
        """
        from .tasks import crear_usuario_teams_async
        from .models import Tarea

        tareas_programadas = 0

        for alumno in queryset:
            # Programar tarea asíncrona
            task = crear_usuario_teams_async.delay(alumno.id)

            # Crear registro de tarea
            Tarea.objects.create(
                tipo=Tarea.TipoTarea.CREAR_USUARIO_TEAMS,
                estado=Tarea.EstadoTarea.PENDING,
                celery_task_id=task.id,
                alumno=alumno,
                usuario=request.user.username if request.user.is_authenticated else None
            )

            tareas_programadas += 1

        # Resumen final
        self.message_user(
            request,
            f"📋 {tareas_programadas} tareas programadas en cola de Celery. "
            f"Revisa la tabla de Tareas Asíncronas para ver credenciales.",
            level=messages.SUCCESS
        )

    @admin.action(description="📧 Enviar email con credenciales")
    def enviar_email_credenciales(self, request, queryset):
        """
        Envía email con credenciales existentes.
        Útil para reenviar credenciales.
        """
        from django.conf import settings

        email_svc = EmailService()
        teams_svc = TeamsService()

        success_count = 0
        error_count = 0

        for alumno in queryset:
            if not alumno.email:
                self.message_user(
                    request,
                    f"⚠️ {alumno.apellido}, {alumno.nombre} no tiene email",
                    level=messages.WARNING
                )
                error_count += 1
                continue

            try:
                # Construir UPN y obtener usuario de Teams
                prefix = settings.ACCOUNT_PREFIX
                upn = f"{prefix}{alumno.dni}@{settings.TEAMS_DOMAIN}"

                # Verificar que el usuario existe en Teams
                user = teams_svc.get_user(upn)
                if not user:
                    self.message_user(
                        request,
                        f"⚠️ {alumno.apellido}, {alumno.nombre}: Usuario {upn} no existe en Teams",
                        level=messages.WARNING
                    )
                    error_count += 1
                    continue

                # Generar nueva contraseña temporal
                new_password = teams_svc.reset_password(upn)
                if not new_password:
                    self.message_user(
                        request,
                        f"❌ Error reseteando contraseña para {upn}",
                        level=messages.ERROR
                    )
                    error_count += 1
                    continue

                # Enviar email con nueva contraseña
                teams_data = {
                    'upn': upn,
                    'password': new_password
                }

                email_sent = email_svc.send_credentials_email(alumno, teams_data)

                if email_sent:
                    self.message_user(
                        request,
                        f"✅ {alumno.apellido}, {alumno.nombre}: Email enviado a {alumno.email}",
                        level=messages.SUCCESS
                    )
                    success_count += 1
                else:
                    self.message_user(
                        request,
                        f"❌ Error enviando email a {alumno.email}",
                        level=messages.ERROR
                    )
                    error_count += 1

            except Exception as e:
                self.message_user(
                    request,
                    f"❌ Error procesando {alumno.apellido}, {alumno.nombre}: {str(e)}",
                    level=messages.ERROR
                )
                error_count += 1

        self.message_user(
            request,
            f"📊 Emails: {success_count} enviados, {error_count} errores",
            level=messages.INFO
        )

    @admin.action(description="🔑 Resetear contraseña Teams")
    def resetear_password_teams(self, request, queryset):
        """
        Resetea la contraseña de Teams para los usuarios seleccionados.
        """
        from django.conf import settings

        teams_svc = TeamsService()

        success_count = 0
        error_count = 0

        for alumno in queryset:
            try:
                prefix = settings.ACCOUNT_PREFIX
                upn = f"{prefix}{alumno.dni}@{settings.TEAMS_DOMAIN}"

                new_password = teams_svc.reset_password(upn)

                if new_password:
                    # Actualizar campos del alumno
                    alumno.email_institucional = upn
                    alumno.teams_password = new_password
                    alumno.save(update_fields=['email_institucional', 'teams_password'])

                    self.message_user(
                        request,
                        f"✅ {alumno.apellido}, {alumno.nombre} - UPN: {upn} - Nueva pass: {new_password}",
                        level=messages.SUCCESS
                    )
                    success_count += 1
                else:
                    self.message_user(
                        request,
                        f"❌ Error reseteando contraseña para {upn}",
                        level=messages.ERROR
                    )
                    error_count += 1

            except Exception as e:
                self.message_user(
                    request,
                    f"❌ Error procesando {alumno.apellido}, {alumno.nombre}: {str(e)}",
                    level=messages.ERROR
                )
                error_count += 1

        self.message_user(
            request,
            f"📊 Contraseñas: {success_count} reseteadas, {error_count} errores",
            level=messages.INFO
        )

    def carreras_display(self, obj):
        """Muestra las carreras del alumno en formato legible."""
        if not obj.carreras_data:
            return "-"

        carreras_list = []
        for carrera in obj.carreras_data:
            nombre = carrera.get("nombre_carrera", "")
            id_carrera = carrera.get("id_carrera", "")
            modalidad = carrera.get("modalidad", "")
            mod_texto = "Presencial" if modalidad == "1" else "Distancia" if modalidad == "2" else modalidad
            carreras_list.append(f"{nombre} ({mod_texto})")

        return ", ".join(carreras_list) if carreras_list else "-"

    carreras_display.short_description = "Carreras"


class CarreraListFilter(admin.SimpleListFilter):
    """Filtro personalizado para filtrar por nombre de carrera."""
    title = 'Carrera'
    parameter_name = 'carrera'

    def lookups(self, request, model_admin):
        """Obtiene lista única de carreras de todos los alumnos."""
        from django.db.models import Q

        # Obtener todas las carreras únicas
        alumnos = Alumno.objects.exclude(carreras_data__isnull=True)
        carreras_set = set()

        for alumno in alumnos:
            if alumno.carreras_data:
                for carrera in alumno.carreras_data:
                    nombre = carrera.get("nombre_carrera")
                    id_carrera = carrera.get("id_carrera")
                    if nombre:
                        carreras_set.add((str(id_carrera), nombre))

        return sorted(carreras_set, key=lambda x: x[1])

    def queryset(self, request, queryset):
        """Filtra los alumnos que tienen la carrera seleccionada."""
        if self.value():
            # Buscar alumnos donde carreras_data contenga el id_carrera
            return queryset.filter(carreras_data__contains=[{"id_carrera": int(self.value())}])
        return queryset


# Re-registrar AlumnoAdmin con el filtro personalizado
admin.site.unregister(Alumno)

@admin.register(Alumno)
class AlumnoAdminWithFilters(AlumnoAdmin):
    """AlumnoAdmin con filtros personalizados."""
    list_filter = ("estado_actual", "modalidad_actual", CarreraListFilter, "cohorte")


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    """Admin para visualizar logs del sistema."""

    list_display = (
        'fecha',
        'tipo_colored',
        'modulo',
        'mensaje_corto',
        'alumno_link',
        'usuario',
    )
    list_filter = (
        'tipo',
        'modulo',
        ('fecha', admin.DateFieldListFilter),
    )
    search_fields = (
        'mensaje',
        'modulo',
        'usuario',
        'alumno__nombre',
        'alumno__apellido',
        'alumno__dni',
    )
    readonly_fields = (
        'tipo',
        'modulo',
        'mensaje',
        'detalles_formatted',
        'alumno',
        'usuario',
        'fecha',
    )
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)

    def has_add_permission(self, request):
        """No permitir agregar logs manualmente."""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir editar logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Permitir eliminar logs (limpieza)."""
        return request.user.is_superuser

    def tipo_colored(self, obj):
        """Muestra el tipo con color."""
        colors = {
            'SUCCESS': 'green',
            'INFO': 'blue',
            'WARNING': 'orange',
            'ERROR': 'red',
            'DEBUG': 'gray',
        }
        color = colors.get(obj.tipo, 'black')
        return f'<span style="color: {color}; font-weight: bold;">{obj.get_tipo_display()}</span>'
    tipo_colored.short_description = 'Tipo'
    tipo_colored.allow_tags = True

    def mensaje_corto(self, obj):
        """Muestra los primeros 100 caracteres del mensaje."""
        if len(obj.mensaje) > 100:
            return obj.mensaje[:100] + '...'
        return obj.mensaje
    mensaje_corto.short_description = 'Mensaje'

    def alumno_link(self, obj):
        """Link al alumno si existe."""
        if obj.alumno:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse('admin:alumnos_alumno_change', args=[obj.alumno.id])
            return format_html('<a href="{}">{}</a>', url, obj.alumno)
        return '-'
    alumno_link.short_description = 'Alumno'

    def detalles_formatted(self, obj):
        """Formatea el JSON de detalles para visualización."""
        if obj.detalles:
            import json
            from django.utils.html import format_html
            formatted = json.dumps(obj.detalles, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted)
        return '-'
    detalles_formatted.short_description = 'Detalles'


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    """Admin para visualizar tareas asíncronas de Celery."""

    list_display = (
        'id',
        'tipo_colored',
        'estado_colored',
        'hora_programada',
        'duracion_formatted',
        'cantidad_entidades',
        'alumno_link',
        'usuario',
    )
    list_filter = (
        'tipo',
        'estado',
        ('hora_programada', admin.DateFieldListFilter),
    )
    search_fields = (
        'celery_task_id',
        'alumno__nombre',
        'alumno__apellido',
        'alumno__dni',
        'usuario',
        'mensaje_error',
    )
    readonly_fields = (
        'tipo',
        'estado',
        'celery_task_id',
        'hora_programada',
        'hora_inicio',
        'hora_fin',
        'cantidad_entidades',
        'detalles_formatted',
        'alumno',
        'usuario',
        'mensaje_error',
        'duracion_formatted',
    )
    fieldsets = (
        ('Información de la Tarea', {
            'fields': ('tipo', 'estado', 'celery_task_id')
        }),
        ('Tiempos', {
            'fields': ('hora_programada', 'hora_inicio', 'hora_fin', 'duracion_formatted')
        }),
        ('Resultados', {
            'fields': ('cantidad_entidades', 'detalles_formatted', 'mensaje_error')
        }),
        ('Contexto', {
            'fields': ('alumno', 'usuario')
        }),
    )
    date_hierarchy = 'hora_programada'
    ordering = ('-hora_programada',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def tipo_colored(self, obj):
        """Muestra el tipo de tarea con color."""
        from django.utils.html import format_html
        color_map = {
            'ingesta_preinscriptos': '#3498db',
            'ingesta_aspirantes': '#2ecc71',
            'ingesta_ingresantes': '#9b59b6',
            'eliminar_cuenta': '#e74c3c',
            'enviar_email': '#f39c12',
            'activar_servicios': '#1abc9c',
            'crear_usuario_teams': '#34495e',
            'resetear_password': '#e67e22',
        }
        color = color_map.get(obj.tipo, '#95a5a6')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_tipo_display()
        )
    tipo_colored.short_description = 'Tipo'
    tipo_colored.admin_order_field = 'tipo'

    def estado_colored(self, obj):
        """Muestra el estado con color."""
        from django.utils.html import format_html
        color_map = {
            'pending': '#f39c12',
            'running': '#3498db',
            'completed': '#27ae60',
            'failed': '#e74c3c',
        }
        icon_map = {
            'pending': '⏳',
            'running': '▶️',
            'completed': '✅',
            'failed': '❌',
        }
        color = color_map.get(obj.estado, '#95a5a6')
        icon = icon_map.get(obj.estado, '❓')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_estado_display()
        )
    estado_colored.short_description = 'Estado'
    estado_colored.admin_order_field = 'estado'

    def alumno_link(self, obj):
        """Link al alumno relacionado."""
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.alumno:
            url = reverse('admin:alumnos_alumno_change', args=[obj.alumno.id])
            return format_html('<a href="{}">{}</a>', url, obj.alumno)
        return '-'
    alumno_link.short_description = 'Alumno'

    def detalles_formatted(self, obj):
        """Muestra detalles en formato JSON."""
        if obj.detalles:
            import json
            from django.utils.html import format_html
            formatted = json.dumps(obj.detalles, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted)
        return '-'
    detalles_formatted.short_description = 'Detalles'

    def duracion_formatted(self, obj):
        """Muestra la duración de la tarea."""
        from django.utils.html import format_html
        duracion = obj.duracion
        if duracion is not None:
            return format_html('{:.2f} seg', duracion)
        elif obj.estado == 'running':
            return format_html('<span style="color: #3498db;">En progreso...</span>')
        return '-'
    duracion_formatted.short_description = 'Duración'


@admin.register(Configuracion)
class ConfiguracionAdmin(admin.ModelAdmin):
    """Admin para configuración del sistema (Singleton)."""

    fieldsets = (
        ('⚙️ Procesamiento en Lotes y Rate Limiting', {
            'fields': (
                'batch_size',
                'rate_limit_teams',
                'rate_limit_moodle',
            ),
            'description': 'Configuración de workflows automáticos. BATCH_SIZE: alumnos por lote. RATE_LIMIT: tareas máximas por minuto.'
        }),
        ('📥 Ingesta Automática - Preinscriptos', {
            'fields': (
                'preinscriptos_dia_inicio',
                'preinscriptos_dia_fin',
                'preinscriptos_frecuencia_segundos',
            ),
            'description': 'Configuración de ingesta automática de preinscriptos. Dejar vacío para no ejecutar.'
        }),
        ('📥 Ingesta Automática - Aspirantes', {
            'fields': (
                'aspirantes_dia_inicio',
                'aspirantes_dia_fin',
                'aspirantes_frecuencia_segundos',
            ),
            'description': 'Configuración de ingesta automática de aspirantes. Dejar vacío para no ejecutar.'
        }),
        ('📥 Ingesta Automática - Ingresantes', {
            'fields': (
                'ingresantes_dia_inicio',
                'ingresantes_dia_fin',
                'ingresantes_frecuencia_segundos',
            ),
            'description': 'Configuración de ingesta automática de ingresantes. Dejar vacío para no ejecutar.'
        }),
        ('🔐 Credenciales Teams/Azure AD', {
            'fields': (
                'teams_tenant_id',
                'teams_client_id',
                'teams_client_secret',
                'account_prefix',
            ),
            'description': 'Credenciales de Teams y prefijo de cuentas. Si están vacías, se usan las variables de entorno. ACCOUNT_PREFIX: "test-a" para testing, "a" para producción.',
            'classes': ('collapse',)
        }),
        ('🎓 Credenciales Moodle', {
            'fields': (
                'moodle_base_url',
                'moodle_wstoken',
            ),
            'description': 'Credenciales de Moodle. Si están vacías, se usan las variables de entorno.',
            'classes': ('collapse',)
        }),
        ('📧 Configuración de Email', {
            'fields': (
                'email_from',
                'email_host',
                'email_port',
                'email_use_tls',
            ),
            'description': 'Configuración SMTP para envío de emails. Si están vacíos, se usan las variables de entorno (DEFAULT_FROM_EMAIL, EMAIL_HOST, etc.).',
            'classes': ('collapse',)
        }),
        ('ℹ️ Metadatos', {
            'fields': (
                'actualizado_en',
                'actualizado_por',
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('actualizado_en', 'actualizado_por')

    def has_add_permission(self, request):
        """Solo puede haber una configuración (Singleton)."""
        return not Configuracion.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """No se puede eliminar la configuración."""
        return False

    def save_model(self, request, obj, form, change):
        """Guarda quién modificó la configuración."""
        obj.actualizado_por = request.user.username
        super().save_model(request, obj, form, change)

    def changelist_view(self, request, extra_context=None):
        """Redirige directamente al formulario de edición."""
        obj = Configuracion.load()
        from django.urls import reverse
        from django.http import HttpResponseRedirect
        url = reverse('admin:alumnos_configuracion_change', args=[obj.pk])
        return HttpResponseRedirect(url)
