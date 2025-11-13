from django.db import models


class Modalidad(models.Model):
    """
    Tabla Modalidades
    id (auto)        -> PK Django
    nombre           -> Nombre
    codigo           -> Codigo
    codigo_uti       -> CodigoUTI (el que viene de la UTI)
    """
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    codigo_uti = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Plan(models.Model):
    """
    Tabla Planes
    idplan           -> id_plan_uti (el identificador que viene de la UTI)
    anio             -> año del plan
    """
    id_plan_uti = models.IntegerField(unique=True, db_index=True)
    anio = models.IntegerField()

    def __str__(self):
        return f"Plan {self.id_plan_uti} ({self.anio})"


class Carrera(models.Model):
    """
    Tabla Carrera
    idplan           -> FK a Plan
    nombre           -> Nombre
    """
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="carreras",
    )
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre


class Materia(models.Model):
    """
    Tabla Materias
    idmaterias       -> id_materia_uti (id externo)
    nombre           -> Nombre
    codigo_corto     -> Codigo Corto
    codigo_uti       -> Codigo UTI
    codigo_plan      -> Codigo Plan (o FK indirecta a Plan si coincide)
    """
    id_materia_uti = models.IntegerField(unique=True, db_index=True)
    nombre = models.CharField(max_length=255)
    codigo_corto = models.CharField(max_length=20, blank=True)
    codigo_uti = models.CharField(max_length=50, blank=True)
    codigo_plan = models.CharField(max_length=50, blank=True)

    # opcional: si después querés unir a Plan de forma fuerte:
    # plan = models.ForeignKey(Plan, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return f"{self.codigo_corto or self.id_materia_uti} - {self.nombre}"


class Comision(models.Model):
    """
    Tabla Comisiones
    idmateria        -> FK a Materia
    nombre           -> Nombre
    codigo_uti       -> Codigo UTI
    codigo           -> Codigo
    modalidad        -> FK a Modalidad
    """
    materia = models.ForeignKey(
        Materia,
        on_delete=models.CASCADE,
        related_name="comisiones",
    )
    nombre = models.CharField(max_length=255)
    codigo_uti = models.CharField(max_length=50, blank=True)
    codigo = models.CharField(max_length=50, blank=True)

    modalidad = models.ForeignKey(
        Modalidad,
        on_delete=models.PROTECT,
        related_name="comisiones",
    )

    def __str__(self):
        return f"{self.materia} - {self.nombre}"

    class Meta:
        verbose_name = "Comisión"
        verbose_name_plural = "Comisiones"


class Alumno(models.Model):
    """
    Tabla alumnos
    tipodoc
    dni
    nombre
    apellido
    email
    localidad
    telefono
    modalidad (id)   -> FK a Modalidad
    """
    tipodoc = models.CharField(max_length=10)
    dni = models.BigIntegerField(unique=True, db_index=True)

    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    localidad = models.CharField(max_length=150, blank=True)
    telefono = models.CharField(max_length=50, blank=True)

    modalidad = models.ForeignKey(
        Modalidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alumnos",
    )

    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.dni})"


class Inscripcion(models.Model):
    """
    Tabla Alumnos_Inscripciones
    idLalumno   -> alumno (FK)
    idMateria   -> materia (FK)
    idComision  -> comision (FK)
    fecha_api   -> FEcha_API
    anio        -> Año
    """
    alumno = models.ForeignKey(
        Alumno,
        on_delete=models.CASCADE,
        related_name="inscripciones",
    )
    materia = models.ForeignKey(
        Materia,
        on_delete=models.PROTECT,
        related_name="inscripciones",
    )
    comision = models.ForeignKey(
        Comision,
        on_delete=models.PROTECT,
        related_name="inscripciones",
    )
    fecha_api = models.DateTimeField()
    anio = models.IntegerField()

    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        # evita duplicados absurdos para misma combinación en el mismo año
        unique_together = ("alumno", "materia", "comision", "anio")
        verbose_name = "Incripción"
        verbose_name_plural = "Incripciones"

    def __str__(self):
        return f"{self.alumno} → {self.materia} [{self.comision}] ({self.anio})"

