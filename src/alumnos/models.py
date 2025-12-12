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
    carreras_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Array de carreras tal como viene de la API UTI/SIAL (id_carrera, nombre_carrera, modalidad, comisiones)"
    )
    teams_password = models.CharField(max_length=255, null=True, blank=True)
    teams_payload = models.JSONField(null=True, blank=True)
    email_payload = models.JSONField(null=True, blank=True)
    moodle_payload = models.JSONField(null=True, blank=True)
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

    @property
    def email(self):
        """Retorna email_institucional si existe, sino email_personal"""
        return self.email_institucional or self.email_personal


class Log(models.Model):
    """Modelo para registrar logs de operaciones del sistema."""

    class TipoLog(models.TextChoices):
        INFO = "INFO", "Información"
        WARNING = "WARNING", "Advertencia"
        ERROR = "ERROR", "Error"
        SUCCESS = "SUCCESS", "Éxito"
        DEBUG = "DEBUG", "Debug"

    tipo = models.CharField(
        max_length=10,
        choices=TipoLog.choices,
        default=TipoLog.INFO,
        db_index=True
    )
    modulo = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Módulo o servicio que generó el log (ej: teams_service, email_service)"
    )
    mensaje = models.TextField(
        help_text="Mensaje descriptivo del evento"
    )
    detalles = models.JSONField(
        null=True,
        blank=True,
        help_text="Información adicional en formato JSON"
    )
    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        help_text="Alumno relacionado con el evento (opcional)"
    )
    usuario = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Usuario que ejecutó la acción (opcional)"
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ("-fecha",)
        verbose_name = "Log de Sistema"
        verbose_name_plural = "Logs de Sistema"
        indexes = [
            models.Index(fields=['-fecha', 'tipo']),
            models.Index(fields=['modulo', '-fecha']),
        ]

    def __str__(self):
        return f"[{self.tipo}] {self.modulo} - {self.fecha.strftime('%Y-%m-%d %H:%M:%S')}"


class Tarea(models.Model):
    """Modelo para trackear tareas asíncronas ejecutadas por Celery."""

    class TipoTarea(models.TextChoices):
        INGESTA_PREINSCRIPTOS = "ingesta_preinscriptos", "Ingesta de Preinscriptos"
        INGESTA_ASPIRANTES = "ingesta_aspirantes", "Ingesta de Aspirantes"
        INGESTA_INGRESANTES = "ingesta_ingresantes", "Ingesta de Ingresantes"
        ELIMINAR_CUENTA = "eliminar_cuenta", "Eliminar Cuenta Externa"
        ENVIAR_EMAIL = "enviar_email", "Enviar Email"
        ACTIVAR_SERVICIOS = "activar_servicios", "Activar Servicios (Teams+Email)"
        CREAR_USUARIO_TEAMS = "crear_usuario_teams", "Crear Usuario en Teams"
        RESETEAR_PASSWORD = "resetear_password", "Resetear Contraseña"

    class EstadoTarea(models.TextChoices):
        PENDING = "pending", "Pendiente"
        RUNNING = "running", "Ejecutando"
        COMPLETED = "completed", "Completada"
        FAILED = "failed", "Fallida"

    tipo = models.CharField(
        max_length=30,
        choices=TipoTarea.choices,
        db_index=True,
        help_text="Tipo de tarea ejecutada"
    )
    estado = models.CharField(
        max_length=15,
        choices=EstadoTarea.choices,
        default=EstadoTarea.PENDING,
        db_index=True,
        help_text="Estado actual de la tarea"
    )
    celery_task_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="ID de la tarea en Celery"
    )
    hora_programada = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Cuándo se creó/programó la tarea"
    )
    hora_inicio = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Cuándo empezó a ejecutarse"
    )
    hora_fin = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Cuándo terminó de ejecutarse"
    )
    cantidad_entidades = models.PositiveIntegerField(
        default=0,
        help_text="Cantidad de entidades afectadas (alumnos creados, emails enviados, etc.)"
    )
    detalles = models.JSONField(
        null=True,
        blank=True,
        help_text="Información adicional sobre la tarea (resultados, errores, etc.)"
    )
    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tareas',
        help_text="Alumno relacionado con la tarea (si aplica)"
    )
    usuario = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Usuario que inició la tarea (opcional)"
    )
    mensaje_error = models.TextField(
        null=True,
        blank=True,
        help_text="Mensaje de error si la tarea falló"
    )

    class Meta:
        ordering = ("-hora_programada",)
        verbose_name = "Tarea Asíncrona"
        verbose_name_plural = "Tareas Asíncronas"
        indexes = [
            models.Index(fields=['-hora_programada', 'estado']),
            models.Index(fields=['tipo', '-hora_programada']),
            models.Index(fields=['estado', 'tipo']),
        ]

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.estado} - {self.hora_programada.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def duracion(self):
        """Retorna la duración de la tarea en segundos si está completada."""
        if self.hora_inicio and self.hora_fin:
            return (self.hora_fin - self.hora_inicio).total_seconds()
        return None


class Configuracion(models.Model):
    """
    Configuración centralizada del sistema.
    Solo debe haber UNA fila en esta tabla (Singleton pattern).
    """

    # Ingesta automática de Preinscriptos
    preinscriptos_dia_inicio = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora para iniciar ingesta de preinscriptos. Vacío = no ejecutar"
    )
    preinscriptos_dia_fin = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora para detener ingesta de preinscriptos. Vacío = sin límite"
    )
    preinscriptos_frecuencia_segundos = models.PositiveIntegerField(
        default=3600,
        help_text="Frecuencia de ingesta de preinscriptos en segundos (default: 3600 = 1 hora)"
    )

    # Ingesta automática de Aspirantes
    aspirantes_dia_inicio = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora para iniciar ingesta de aspirantes. Vacío = no ejecutar"
    )
    aspirantes_dia_fin = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora para detener ingesta de aspirantes. Vacío = sin límite"
    )
    aspirantes_frecuencia_segundos = models.PositiveIntegerField(
        default=3600,
        help_text="Frecuencia de ingesta de aspirantes en segundos (default: 3600 = 1 hora)"
    )

    # Ingesta automática de Ingresantes
    ingresantes_dia_inicio = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora para iniciar ingesta de ingresantes. Vacío = no ejecutar"
    )
    ingresantes_dia_fin = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora para detener ingesta de ingresantes. Vacío = sin límite"
    )
    ingresantes_frecuencia_segundos = models.PositiveIntegerField(
        default=3600,
        help_text="Frecuencia de ingesta de ingresantes en segundos (default: 3600 = 1 hora)"
    )

    # Configuración de procesamiento en lotes
    batch_size = models.PositiveIntegerField(
        default=20,
        help_text="Cantidad de alumnos a procesar por lote (recomendado: 10-30)"
    )
    rate_limit_teams = models.PositiveIntegerField(
        default=10,
        help_text="Máximo de tareas Teams por minuto (recomendado: 5-15, no exceder 20)"
    )
    rate_limit_moodle = models.PositiveIntegerField(
        default=30,
        help_text="Máximo de tareas Moodle por minuto (recomendado: 20-50)"
    )

    # Tokens y credenciales (pueden anular variables de entorno)
    teams_tenant_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Tenant ID de Azure AD (GUID). Si está vacío, usa variable de entorno"
    )
    teams_client_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Client ID de Teams App. Si está vacío, usa variable de entorno"
    )
    teams_client_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="Client Secret de Teams App. Si está vacío, usa variable de entorno"
    )
    account_prefix = models.CharField(
        max_length=20,
        blank=True,
        help_text="Prefijo para cuentas (ej: 'test-a' para testing, 'a' para producción). Si está vacío, usa variable de entorno"
    )
    moodle_base_url = models.URLField(
        max_length=255,
        blank=True,
        help_text="URL base de Moodle. Si está vacío, usa variable de entorno"
    )
    moodle_wstoken = models.CharField(
        max_length=255,
        blank=True,
        help_text="Token de Moodle WebServices. Si está vacío, usa variable de entorno"
    )
    email_from = models.EmailField(
        max_length=255,
        blank=True,
        help_text="Email remitente para notificaciones. Si está vacío, usa DEFAULT_FROM_EMAIL de entorno"
    )
    email_host = models.CharField(
        max_length=255,
        blank=True,
        help_text="Servidor SMTP para envío de emails. Si está vacío, usa EMAIL_HOST de entorno"
    )
    email_port = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Puerto SMTP (ej: 587 para TLS, 465 para SSL). Si está vacío, usa EMAIL_PORT de entorno"
    )
    email_use_tls = models.BooleanField(
        null=True,
        blank=True,
        help_text="Usar TLS para conexión SMTP. Si es NULL, usa EMAIL_USE_TLS de entorno"
    )

    # Metadatos
    actualizado_en = models.DateTimeField(auto_now=True)
    actualizado_por = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuración del Sistema"

    def __str__(self):
        return "Configuración del Sistema"

    def save(self, *args, **kwargs):
        """Asegura que solo haya una fila (Singleton)."""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Previene eliminación de la configuración."""
        pass

    @classmethod
    def load(cls):
        """Obtiene la configuración (crea una si no existe)."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
