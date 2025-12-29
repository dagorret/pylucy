# Lucy AMS - Academic Management System

**Versión:** 0.98
**Autor:** Carlos Dagorret
**Institución:** Facultad de Ciencias Económicas, Universidad Nacional de Río Cuarto (UNRC)
**Licencia:** MIT
**Fecha:** Diciembre 2025

---

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [¿Qué es un AMS?](#qué-es-un-ams)
3. [Finalidad del Sistema](#finalidad-del-sistema)
4. [Arquitectura y Componentes](#arquitectura-y-componentes)
5. [Conceptos Fundamentales](#conceptos-fundamentales)
6. [Integración con Servicios Externos](#integración-con-servicios-externos)
7. [Sistema de Procesamiento Asíncrono](#sistema-de-procesamiento-asíncrono)
8. [Flujo de Trabajo](#flujo-de-trabajo)
9. [Tecnologías y Stack Técnico](#tecnologías-y-stack-técnico)
10. [Referencias y Bibliografía](#referencias-y-bibliografía)

---

## Introducción

Lucy AMS es un sistema de gestión académica (Academic Management System) desarrollado específicamente para automatizar y centralizar los procesos de gestión de estudiantes en instituciones de educación superior. El sistema fue diseñado e implementado para la Facultad de Ciencias Económicas de la Universidad Nacional de Río Cuarto (FCE-UNRC), Argentina.

El sistema opera como una plataforma integradora que conecta múltiples servicios externos, proporcionando una capa de automatización para tareas que tradicionalmente requerían intervención manual extensiva: creación de cuentas de usuario, enrollamiento en plataformas virtuales, gestión de credenciales, y notificaciones por correo electrónico.

---

## ¿Qué es un AMS?

### Definición

Un Academic Management System (AMS) es un sistema de información diseñado para gestionar procesos administrativos y académicos en instituciones educativas. Estos sistemas son también conocidos como Student Information Systems (SIS) o Learning Management Systems (LMS) cuando se enfocan específicamente en la gestión del aprendizaje.

### Características Principales de un AMS

Un AMS típico proporciona funcionalidades para:

- **Gestión de Estudiantes**: Administración de datos personales, matrículas, historial académico
- **Gestión de Cursos**: Planificación académica, asignación de docentes, horarios
- **Evaluación y Calificaciones**: Registro de notas, cálculo de promedios, certificaciones
- **Comunicaciones**: Notificaciones automáticas, mensajería interna
- **Integración de Servicios**: Conexión con sistemas institucionales y plataformas externas
- **Reportes y Analytics**: Generación de estadísticas e indicadores académicos

### Diferencias con otros Sistemas Educativos

**LMS (Learning Management System):**
- Enfocado en la entrega de contenido educativo
- Gestión de materiales de estudio, actividades, evaluaciones
- Ejemplos: Moodle, Canvas, Blackboard

**SIS (Student Information System):**
- Enfocado en datos administrativos del estudiante
- Gestión de matrículas, calificaciones, historial académico
- Ejemplos: Banner, PeopleSoft Campus Solutions

**AMS (Academic Management System):**
- Integración de ambos enfoques
- Gestión académica y administrativa centralizada
- Puede actuar como orquestador de múltiples sistemas

Lucy AMS funciona como un **orquestador** o **middleware** que integra sistemas existentes (UTI/SIAL para datos estudiantiles, Microsoft Teams para comunicación, Moodle para gestión de aprendizaje) proporcionando automatización y flujos de trabajo unificados.

---

## Finalidad del Sistema

### Objetivos Principales

**1. Automatización de Procesos Administrativos**

Eliminar tareas repetitivas y propensas a errores humanos mediante automatización:
- Creación masiva de cuentas de usuario en Microsoft Teams
- Enrollamiento automático de estudiantes en cursos de Moodle
- Generación y distribución de credenciales de acceso
- Notificaciones automáticas por correo electrónico

**2. Integración de Sistemas Heterogéneos**

Conectar sistemas que operan de forma aislada:
- **UTI/SIAL**: Sistema de información académica institucional (fuente de datos de estudiantes)
- **Microsoft Teams**: Plataforma de comunicación y colaboración
- **Moodle**: Plataforma de gestión del aprendizaje (LMS)
- **SMTP/Email**: Sistema de notificaciones

**3. Gestión Centralizada**

Proporcionar un punto único de administración para:
- Consultar estado de cuentas de estudiantes
- Ejecutar acciones masivas sobre grupos de estudiantes
- Monitorear tareas en ejecución
- Visualizar logs y auditoría de operaciones

**4. Reducción de Tiempos Operativos**

Transformar procesos que tomaban días u horas en operaciones de minutos:
- Creación manual de 500+ cuentas: ~40 horas → <30 minutos automatizado
- Enrollamiento manual en múltiples cursos: ~20 horas → <15 minutos automatizado

### Casos de Uso Principales

**Ingreso de Nuevos Estudiantes (Aspirantes/Ingresantes)**
1. Ingesta automática desde sistema UTI/SIAL
2. Creación de cuentas en Microsoft Teams con UPN institucional
3. Generación de contraseñas temporales seguras
4. Envío de emails de bienvenida con credenciales
5. Enrollamiento en cursos de ingreso en Moodle

**Gestión de Estudiantes Regulares**
1. Actualización de datos desde UTI/SIAL
2. Enrollamiento en cursos del ciclo académico actual
3. Gestión de contraseñas (reseteo, regeneración)
4. Sincronización de estados entre sistemas

**Operaciones Administrativas**
1. Exportación/importación de configuraciones
2. Backups de base de datos
3. Monitoreo de tareas y procesos
4. Auditoría de operaciones

---

## Arquitectura y Componentes

### Arquitectura General

Lucy AMS está construido siguiendo una arquitectura de microservicios containerizados con Docker, implementando el patrón **Service-Oriented Architecture (SOA)** con procesamiento asíncrono basado en colas.

```
┌─────────────────────────────────────────────────────────────┐
│                     Lucy AMS Architecture                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │      │  Admin Panel │      │   REST API   │
│   (Django)   │◄────►│   (Django    │◄────►│   (Future)   │
│              │      │    Admin)    │      │              │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Django Backend │
                    │   (Business     │
                    │     Logic)      │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │ Celery  │         │  Redis  │         │  Postgres│
   │ Workers │◄───────►│ (Broker)│         │   (DB)   │
   └────┬────┘         └─────────┘         └──────────┘
        │
   ┌────▼────┐
   │ Celery  │
   │  Beat   │
   │(Scheduler)│
   └─────────┘

External Services:
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  UTI/SIAL    │  │   MS Teams   │  │    Moodle    │
│   API        │  │  (Graph API) │  │  Web Services│
└──────────────┘  └──────────────┘  └──────────────┘
```

### Componentes del Sistema

#### 1. Django Web Application

**Propósito:** Framework web principal que proporciona la capa de presentación y lógica de negocio.

**Funcionalidades:**
- Gestión de modelos de datos (ORM)
- Panel de administración personalizado
- Autenticación y autorización
- Validación de datos
- Logging y auditoría

**Repositorio:** https://github.com/django/django
**Documentación:** https://docs.djangoproject.com/

**Configuración en Lucy:**
```python
# Django 5.2.9
# Uso de ORM para PostgreSQL
# Admin personalizado con acciones masivas
# Middleware para logging automático
```

#### 2. PostgreSQL Database

**Propósito:** Sistema de gestión de base de datos relacional para almacenamiento persistente.

**Esquema de Datos Principal:**
- **Alumno**: Datos del estudiante, estado de cuentas (Teams, Moodle)
- **Configuracion**: Configuración del sistema y credenciales de servicios
- **Log**: Registro de auditoría de todas las operaciones
- **TareaPersonalizada**: Definición de tareas programadas
- **Curso**: Información de cursos académicos

**Repositorio:** https://github.com/postgres/postgres
**Versión:** PostgreSQL 16

#### 3. Redis

**Propósito:** Base de datos en memoria utilizada como message broker y cache.

**Usos en Lucy:**
- **Message Broker**: Cola de mensajes para Celery
- **Result Backend**: Almacenamiento de resultados de tareas
- **Cache**: Almacenamiento temporal de datos frecuentemente accedidos

**Repositorio:** https://github.com/redis/redis
**Versión:** Redis 7

#### 4. Celery Worker

**Propósito:** Sistema de procesamiento de tareas asíncronas distribuidas.

**Repositorio:** https://github.com/celery/celery
**Documentación:** https://docs.celeryproject.org/

Celery es un sistema de cola de tareas distribuido enfocado en procesamiento en tiempo real, con soporte para programación de tareas.

**Conceptos Clave:**

**Worker (Trabajador):**
- Proceso que ejecuta tareas de forma asíncrona
- Puede escalar horizontalmente (múltiples workers)
- Consume mensajes de las colas en Redis
- Ejecuta tareas definidas en `tasks.py`

**Task (Tarea):**
- Unidad de trabajo que se ejecuta de forma asíncrona
- Decoradas con `@shared_task` o `@app.task`
- Pueden tener reintentos, timeouts, rate limits

**Queue (Cola):**
- Canal de comunicación entre productor y consumidor
- Redis actúa como broker de mensajes
- Implementa patrón FIFO (First In, First Out)
- Permite priorización de tareas

**Tareas Implementadas en Lucy:**
```python
# alumnos/tasks.py

@shared_task
def crear_usuario_teams_task(alumno_id):
    """Crea usuario en Microsoft Teams de forma asíncrona"""

@shared_task
def enrollar_moodle_task(alumno_id, curso_ids):
    """Enrolla estudiante en cursos de Moodle"""

@shared_task
def ingestar_aspirantes_task():
    """Ingesta masiva de aspirantes desde UTI/SIAL"""

@shared_task
def enviar_email_task(destinatario, asunto, cuerpo_html):
    """Envía correo electrónico de forma asíncrona"""
```

**Flujo de Ejecución de una Tarea:**

```
1. Django produce mensaje
   alumno.crear_teams_async()
   └─► task.delay(alumno_id)

2. Redis almacena en cola
   ┌──────────────┐
   │ Queue: tasks │
   │ [msg1, msg2] │
   └──────────────┘

3. Celery Worker consume
   Worker lee mensaje
   └─► Ejecuta función
       └─► Llama API Teams
           └─► Guarda resultado

4. Resultado almacenado
   Redis result backend
   └─► Success/Failure
```

**Ventajas del Procesamiento Asíncrono:**
- **No Bloquea UI**: Usuario no espera tareas largas
- **Resilencia**: Reintentos automáticos en caso de falla
- **Escalabilidad**: Múltiples workers procesan en paralelo
- **Rate Limiting**: Control de velocidad de peticiones a APIs externas

#### 5. Celery Beat

**Propósito:** Scheduler distribuido para tareas periódicas (cron-like).

Celery Beat es el planificador de tareas periódicas de Celery, equivalente a cron pero integrado con el sistema de colas.

**Conceptos de Celery Beat:**

**Beat Scheduler:**
- Proceso separado que genera tareas según calendario
- Lee configuración desde base de datos (django_celery_beat)
- Envía tareas a las colas en los horarios programados

**Periodic Tasks:**
- Tareas configuradas para ejecutarse en intervalos regulares
- Configurables desde Django Admin
- Tipos de schedule:
  - **Crontab**: Expresiones cron (ej: "0 2 * * *" = 2 AM diario)
  - **Interval**: Cada N segundos/minutos/horas
  - **Solar**: Basado en eventos solares (amanecer/atardecer)

**Tareas Periódicas en Lucy:**

```python
# Configuradas en django_celery_beat.models.PeriodicTask

# Sincronización diaria de estudiantes
Schedule: Crontab(hour=2, minute=0)  # 2:00 AM
Task: ingestar_aspirantes_task
Descripción: Obtiene nuevos estudiantes desde UTI/SIAL

# Limpieza de logs antiguos
Schedule: Interval(days=7)  # Cada 7 días
Task: cleanup_old_logs_task
Descripción: Elimina logs con más de 90 días

# Verificación de cuentas Teams
Schedule: Crontab(hour=6, minute=0, day_of_week='1')  # Lunes 6 AM
Task: verificar_estado_teams_task
Descripción: Verifica estado de cuentas en Microsoft Teams
```

**Arquitectura Beat + Worker:**

```
┌────────────────┐
│  Celery Beat   │
│  (Scheduler)   │
└───────┬────────┘
        │ Envía tarea según schedule
        │
        ▼
┌────────────────┐
│     Redis      │
│   (Broker)     │
└───────┬────────┘
        │ Worker consume tarea
        │
        ▼
┌────────────────┐
│ Celery Worker  │
│  (Executor)    │
└────────────────┘
```

**Diferencia Beat vs Worker:**

| Aspecto | Celery Beat | Celery Worker |
|---------|-------------|---------------|
| **Función** | Planifica tareas | Ejecuta tareas |
| **Cantidad** | 1 instancia única | N instancias (escalable) |
| **Trigger** | Basado en tiempo | Basado en eventos (mensajes) |
| **Persistencia** | Guarda estado en DB | Stateless |

**Repositorio:** https://github.com/celery/django-celery-beat

#### 6. Nginx (Producción)

**Propósito:** Servidor web HTTP y proxy inverso.

**Funcionalidades:**
- Servir archivos estáticos (CSS, JS, imágenes)
- Proxy a Gunicorn (Django)
- Terminación SSL/TLS
- Load balancing
- Compresión gzip

**Repositorio:** https://github.com/nginx/nginx

#### 7. MailHog (Testing)

**Propósito:** Servidor SMTP falso para capturar emails en ambiente de desarrollo.

**Funcionalidades:**
- Captura todos los emails enviados
- Interfaz web para visualizar emails
- No envía emails reales al exterior

**Repositorio:** https://github.com/mailhog/MailHog

---

## Conceptos Fundamentales

### 1. Integración de Sistemas

**API Integration Pattern:**

Lucy implementa el patrón de integración mediante APIs REST y SOAP:

```python
# Patrón de servicio abstracto
class ExternalService:
    def authenticate(self):
        """Autenticación con servicio externo"""

    def create_user(self, user_data):
        """Crear usuario en servicio externo"""

    def get_user(self, user_id):
        """Obtener datos de usuario"""
```

**Service Layer Pattern:**

Cada integración está encapsulada en un servicio dedicado:
- `TeamsService`: Interacción con Microsoft Graph API
- `MoodleService`: Interacción con Moodle Web Services
- `SIALService`: Interacción con API UTI/SIAL
- `EmailService`: Envío de correos con plantillas

### 2. Idempotencia

Las operaciones están diseñadas para ser idempotentes: ejecutar la misma operación múltiples veces produce el mismo resultado.

```python
# Ejemplo: Crear usuario en Teams
def crear_usuario_teams(alumno):
    # 1. Verificar si ya existe
    if alumno.teams_user_id:
        return {"status": "already_exists", "user_id": alumno.teams_user_id}

    # 2. Crear solo si no existe
    user = teams_api.create_user(...)
    alumno.teams_user_id = user.id
    alumno.save()

    return {"status": "created", "user_id": user.id}
```

### 3. Rate Limiting

Control de velocidad de peticiones a APIs externas para respetar límites de servicio:

```python
# Configuración de rate limits
RATE_LIMIT_TEAMS = 10  # 10 requests/segundo
RATE_LIMIT_MOODLE = 30  # 30 requests/segundo

# Implementación con throttling
import time
from datetime import datetime

class RateLimiter:
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    def wait_if_needed(self):
        now = datetime.now()
        # Limpiar requests antiguos
        self.requests = [r for r in self.requests
                        if (now - r).seconds < self.time_window]

        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]).seconds
            time.sleep(sleep_time)

        self.requests.append(now)
```

### 4. Auditoría y Logging

Todas las operaciones se registran en la base de datos para trazabilidad:

```python
# Modelo de Log
class Log(models.Model):
    tipo = models.CharField(max_length=50)  # INFO, WARNING, ERROR
    operacion = models.CharField(max_length=100)  # crear_teams, enrollar_moodle
    alumno = models.ForeignKey(Alumno)
    mensaje = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['alumno', '-timestamp']),
            models.Index(fields=['tipo', '-timestamp']),
        ]
```

### 5. Transaccionalidad

Operaciones críticas están envueltas en transacciones de base de datos:

```python
from django.db import transaction

@transaction.atomic
def activar_estudiante_completo(alumno):
    """Activa estudiante en todos los servicios de forma atómica"""
    try:
        # 1. Crear en Teams
        teams_result = crear_usuario_teams(alumno)

        # 2. Enrollar en Moodle
        moodle_result = enrollar_en_cursos(alumno)

        # 3. Enviar emails
        enviar_credenciales(alumno)

        # Si todo OK, commit automático
        return True

    except Exception as e:
        # Si falla algo, rollback automático
        Log.objects.create(tipo='ERROR', mensaje=str(e))
        raise
```

---

## Integración con Servicios Externos

### Microsoft Teams (Azure AD / Microsoft Graph API)

**¿Qué es Microsoft Teams?**

Microsoft Teams es una plataforma de comunicación y colaboración desarrollada por Microsoft como parte de la familia de productos Office 365 / Microsoft 365. Combina chat empresarial, videoconferencias, almacenamiento de archivos e integración de aplicaciones.

**Componentes de Teams:**
- **Azure Active Directory (Azure AD)**: Directorio de identidades en la nube
- **Microsoft Graph API**: API unificada para acceder a servicios Microsoft 365
- **Teams Application**: Cliente de Teams (web, desktop, mobile)

**Uso en Lucy AMS:**

Lucy crea y gestiona usuarios en Azure AD que luego pueden acceder a Microsoft Teams.

**Operaciones Implementadas:**

```python
# 1. Crear usuario
POST https://graph.microsoft.com/v1.0/users
Body: {
    "accountEnabled": true,
    "displayName": "Juan Pérez",
    "mailNickname": "jperez",
    "userPrincipalName": "a12345678@eco.unrc.edu.ar",
    "passwordProfile": {
        "password": "Temp@Pass123",
        "forceChangePasswordNextSignIn": true
    }
}

# 2. Resetear contraseña
PATCH https://graph.microsoft.com/v1.0/users/{user-id}
Body: {
    "passwordProfile": {
        "password": "NewTemp@Pass456",
        "forceChangePasswordNextSignIn": true
    }
}

# 3. Eliminar usuario
DELETE https://graph.microsoft.com/v1.0/users/{user-id}
```

**Autenticación:**

Lucy utiliza OAuth 2.0 con Client Credentials Flow:

```python
# 1. Obtener token de acceso
POST https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token
Body:
    client_id={client-id}
    client_secret={client-secret}
    scope=https://graph.microsoft.com/.default
    grant_type=client_credentials

# 2. Usar token en requests
Headers:
    Authorization: Bearer {access-token}
```

**Referencia:** https://docs.microsoft.com/graph/api/overview

### Moodle Web Services

**¿Qué es Moodle?**

Moodle (Modular Object-Oriented Dynamic Learning Environment) es un sistema de gestión del aprendizaje (LMS) de código abierto. Es una de las plataformas educativas más utilizadas a nivel mundial, con más de 300 millones de usuarios.

**Características Principales:**
- Gestión de cursos y actividades
- Foros de discusión
- Tareas y evaluaciones
- Recursos educativos
- Sistema de calificaciones
- Plugins y extensiones

**Arquitectura de Moodle:**
- Núcleo en PHP
- Base de datos (PostgreSQL, MySQL, MariaDB)
- Sistema de plugins modular
- Web Services API (REST, SOAP, XML-RPC)

**Uso en Lucy AMS:**

Lucy enrolla automáticamente estudiantes en cursos de Moodle usando la API de Web Services.

**Operaciones Implementadas:**

```python
# 1. Obtener usuario por email
wsfunction: core_user_get_users_by_field
field: email
values: ["estudiante@eco.unrc.edu.ar"]

# 2. Obtener ID de curso
wsfunction: core_course_get_courses_by_field
field: shortname
value: "INGRESO-2024"

# 3. Enrollar usuario en curso
wsfunction: enrol_manual_enrol_users
enrolments: [
    {
        "roleid": 5,  # Estudiante
        "userid": 12345,
        "courseid": 678
    }
]
```

**Autenticación:**

Moodle utiliza tokens de acceso permanentes:

```python
# Cada request incluye el token
https://moodle.ejemplo.com/webservice/rest/server.php?
    wstoken={token}&
    wsfunction=core_user_get_users_by_field&
    moodlewsrestformat=json&
    field=email&
    values[0]=estudiante@ejemplo.com
```

**Métodos de Autenticación en Moodle:**

Lucy soporta tres métodos de autenticación para estudiantes en Moodle:

1. **Manual**: Usuario y contraseña nativos de Moodle
2. **OAuth2**: Autenticación mediante Microsoft Teams (Single Sign-On)
3. **OIDC**: OpenID Connect (estándar recomendado)

**Referencia:** https://docs.moodle.org/dev/Web_services

### Sistema UTI/SIAL

**¿Qué es UTI/SIAL?**

UTI (Unidad de Tecnologías de la Información) y SIAL (Sistema de Información Académica y Legajos) son sistemas institucionales de la UNRC que gestionan datos académicos y administrativos de estudiantes.

**Funcionalidad:**

Lucy consume datos de estudiantes (aspirantes e ingresantes) desde la API REST del sistema UTI/SIAL:

```python
# Obtener lista de aspirantes
GET https://sisinfo.unrc.edu.ar/v1/api/aspirantes/

Response: [
    {
        "dni": "12345678",
        "apellido": "Pérez",
        "nombre": "Juan",
        "email_personal": "juan@gmail.com",
        "email_institucional": "juan.perez@estudiantes.unrc.edu.ar",
        "carrera": "Contador Público"
    },
    ...
]
```

**Autenticación:**

HTTP Basic Authentication:

```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.get(
    'https://sisinfo.unrc.edu.ar/v1/api/aspirantes/',
    auth=HTTPBasicAuth('usuario', 'contraseña')
)
```

---

## Sistema de Procesamiento Asíncrono

### Arquitectura de Colas

Lucy implementa un sistema de colas basado en el patrón **Producer-Consumer** con Celery y Redis.

**Componentes:**

```
┌──────────────┐
│  Producer    │  Django views/admin actions
│  (Django)    │  └─► Genera tareas
└──────┬───────┘
       │ .delay() o .apply_async()
       ▼
┌──────────────┐
│    Broker    │  Redis
│   (Queue)    │  └─► Almacena mensajes
└──────┬───────┘
       │ Consume mensajes
       ▼
┌──────────────┐
│  Consumer    │  Celery Workers
│  (Worker)    │  └─► Ejecuta tareas
└──────┬───────┘
       │ Almacena resultado
       ▼
┌──────────────┐
│   Result     │  Redis / PostgreSQL
│  Backend     │  └─► Guarda estado/resultado
└──────────────┘
```

### Tipos de Tareas

**1. Tareas Individuales (Single Task)**

Operaciones sobre un solo estudiante:

```python
# Crear usuario Teams para un alumno
from alumnos.tasks import crear_usuario_teams_task

resultado = crear_usuario_teams_task.delay(alumno_id=123)

# Verificar estado
if resultado.ready():
    print(f"Resultado: {resultado.result}")
else:
    print(f"Estado: {resultado.state}")
```

**2. Tareas Masivas (Batch Tasks)**

Operaciones sobre múltiples estudiantes con procesamiento por lotes:

```python
# Activar Teams para 500 alumnos
from alumnos.tasks import activar_teams_masivo_task

resultado = activar_teams_masivo_task.delay(
    alumnos_ids=[1, 2, 3, ..., 500],
    batch_size=20  # Procesar de a 20
)

# Procesamiento interno:
# Lote 1: alumnos 1-20   → 20 tareas paralelas
# Lote 2: alumnos 21-40  → 20 tareas paralelas
# ...
# Lote 25: alumnos 481-500 → 20 tareas paralelas
```

**3. Tareas Periódicas (Scheduled Tasks)**

Tareas ejecutadas automáticamente según calendario:

```python
# Configurada en Celery Beat
@app.task
def ingestar_aspirantes_diario():
    """Se ejecuta todos los días a las 2 AM"""
    aspirantes = obtener_desde_sial()
    for asp in aspirantes:
        Alumno.objects.get_or_create(dni=asp['dni'], defaults=asp)
```

### Gestión de Errores y Reintentos

```python
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60  # 60 segundos
)
def tarea_con_reintentos(self, alumno_id):
    try:
        # Operación que puede fallar
        resultado = api_externa.crear_usuario(alumno_id)
        return resultado

    except APITemporaryError as e:
        # Error temporal: reintentar
        raise self.retry(exc=e, countdown=60)

    except APIPermanentError as e:
        # Error permanente: no reintentar
        Log.objects.create(
            tipo='ERROR',
            mensaje=f'Error permanente: {e}'
        )
        raise
```

### Monitoreo de Tareas

```python
# Desde Django shell o código
from celery.result import AsyncResult

# Obtener estado de tarea por ID
task_id = "550e8400-e29b-41d4-a716-446655440000"
result = AsyncResult(task_id)

print(f"Estado: {result.state}")
# Estados posibles: PENDING, STARTED, SUCCESS, FAILURE, RETRY

if result.successful():
    print(f"Resultado: {result.result}")
elif result.failed():
    print(f"Error: {result.info}")
```

---

## Flujo de Trabajo

### Caso: Ingreso de Aspirantes

**Escenario:** Inicia el período de inscripción para nuevos estudiantes.

**Flujo Completo:**

```
1. INGESTA AUTOMÁTICA (Scheduled Task - Celery Beat)
   ├─► Celery Beat ejecuta: ingestar_aspirantes_task()
   ├─► Se conecta a API SIAL/UTI
   ├─► Obtiene lista de aspirantes nuevos
   └─► Crea registros en tabla Alumno

2. REVISIÓN ADMINISTRATIVA (Django Admin)
   ├─► Admin revisa lista de aspirantes
   ├─► Selecciona aspirantes a activar
   └─► Ejecuta acción: "Activar Teams + Enviar Email"

3. CREACIÓN EN TEAMS (Celery Worker)
   ├─► Worker procesa tarea: crear_usuario_teams_task()
   ├─► Genera UPN: a{DNI}@eco.unrc.edu.ar
   ├─► Genera contraseña temporal aleatoria
   ├─► Llama Microsoft Graph API
   ├─► Guarda teams_user_id en Alumno
   └─► Registra operación en Log

4. ENVÍO DE CREDENCIALES (Celery Worker)
   ├─► Worker procesa tarea: enviar_email_credenciales_task()
   ├─► Obtiene plantilla HTML desde Configuracion
   ├─► Reemplaza variables: {nombre}, {apellido}, {upn}, {password}
   ├─► Envía email vía SMTP
   └─► Registra envío en Log

5. ENROLLAMIENTO EN MOODLE (Admin Action)
   ├─► Admin ejecuta acción: "Enrollar en Moodle"
   ├─► Worker procesa tarea: enrollar_moodle_task()
   ├─► Busca usuario en Moodle por email
   ├─► Enrolla en cursos configurados (ej: INGRESO-2024)
   ├─► Guarda moodle_user_id en Alumno
   └─► Opcionalmente envía email de bienvenida

6. VERIFICACIÓN
   ├─► Admin consulta estado en panel
   ├─► Verifica logs de operación
   └─► Confirma cuentas creadas correctamente
```

**Diagrama de Secuencia:**

```
┌──────┐  ┌──────┐  ┌────────┐  ┌───────┐  ┌────────┐  ┌────────┐
│ Beat │  │Django│  │ Celery │  │ Teams │  │ Moodle │  │ Email  │
│      │  │Admin │  │ Worker │  │  API  │  │  API   │  │  SMTP  │
└───┬──┘  └──┬───┘  └───┬────┘  └───┬───┘  └───┬────┘  └───┬────┘
    │ Trigger│       │        │          │           │
    │────────►       │        │          │           │
    │ 2 AM   │       │        │          │           │
    │        │ Task  │        │          │           │
    │        ├───────►        │          │           │
    │        │       │ Create │          │           │
    │        │       ├────────►          │           │
    │        │       │        │ Success  │           │
    │        │       ◄────────┤          │           │
    │        │       │        │          │           │
    │        │ Email │        │          │           │
    │        ├───────►        │          │           │
    │        │       │ Send   │          │           │
    │        │       ├─────────────────────────────► │
    │        │       │        │          │           │
    │        │ Enroll│        │          │           │
    │        ├───────►        │          │           │
    │        │       │ Search │          │           │
    │        │       ├────────────────────►          │
    │        │       │        │          │ Found    │
    │        │       ◄────────────────────┤          │
    │        │       │ Enroll │          │           │
    │        │       ├────────────────────►          │
    │        │       │        │          │ Success  │
    │        │       ◄────────────────────┤          │
```

---

## Tecnologías y Stack Técnico

### Backend

| Tecnología | Versión | Propósito | Repositorio |
|------------|---------|-----------|-------------|
| **Python** | 3.12+ | Lenguaje principal | https://github.com/python/cpython |
| **Django** | 5.2.9 | Framework web | https://github.com/django/django |
| **Celery** | 5.6+ | Procesamiento asíncrono | https://github.com/celery/celery |
| **django-celery-beat** | 2.7+ | Scheduler de tareas | https://github.com/celery/django-celery-beat |
| **PostgreSQL** | 16 | Base de datos relacional | https://github.com/postgres/postgres |
| **Redis** | 7 | Message broker y cache | https://github.com/redis/redis |

### Librerías Python Principales

```python
# requirements.txt

# Framework
Django==5.2.9
gunicorn==23.0.0

# Base de datos
psycopg2-binary==2.9.10

# Celery y tareas asíncronas
celery==5.6.4
redis==6.1.3
django-celery-beat==2.7.0

# APIs externas
requests==2.32.3
msal==1.31.1  # Microsoft Authentication Library

# Utilidades
python-dotenv==1.0.1
pytz==2024.1
```

### Frontend

| Tecnología | Propósito |
|------------|-----------|
| **Django Templates** | Renderizado de HTML |
| **Tailwind CSS** | Framework CSS (landing page) |
| **Django Admin** | Panel de administración |

### Infraestructura

| Tecnología | Propósito | Repositorio |
|------------|-----------|-------------|
| **Docker** | Containerización | https://github.com/docker |
| **Docker Compose** | Orquestación de contenedores | https://github.com/docker/compose |
| **Nginx** | Servidor web / Proxy reverso | https://github.com/nginx/nginx |

### Herramientas de Desarrollo

| Herramienta | Propósito |
|-------------|-----------|
| **Git** | Control de versiones |
| **MailHog** | Testing de emails |
| **pgAdmin** | Administración PostgreSQL |

---

## Referencias y Bibliografía

### Academic Management Systems

**Artículos Académicos:**

1. Watson, W. R., & Watson, S. L. (2007). *An Argument for Clarity: What are Learning Management Systems, What are They Not, and What Should They Become?* TechTrends, 51(2), 28-34.
   - DOI: 10.1007/s11528-007-0023-y

2. Lonn, S., & Teasley, S. D. (2009). *Saving time or innovating practice: Investigating perceptions and uses of Learning Management Systems.* Computers & Education, 53(3), 686-694.
   - DOI: 10.1016/j.compedu.2009.04.008

3. Al-Busaidi, K. A., & Al-Shihi, H. (2010). *Instructors' Acceptance of Learning Management Systems: A Theoretical Framework.* Communications of the IBIMA, 2010.

**Recursos Web:**

1. **UNESCO - ICT in Education**
   - URL: https://www.unesco.org/en/digital-education
   - Descripción: Políticas y buenas prácticas en tecnología educativa

2. **eLearning Industry - Academic Management Systems**
   - URL: https://elearningindustry.com/directory/software-categories/learning-management-systems
   - Descripción: Comparativas y análisis de sistemas de gestión académica

### Moodle

**Documentación Oficial:**

1. **Moodle Documentation**
   - URL: https://docs.moodle.org/
   - Descripción: Documentación completa de Moodle

2. **Moodle Developer Documentation**
   - URL: https://docs.moodle.org/dev/
   - Descripción: Documentación para desarrolladores

3. **Moodle Web Services API**
   - URL: https://docs.moodle.org/dev/Web_services
   - Descripción: Referencia completa de Web Services

**Repositorios:**

1. **Moodle Core**
   - URL: https://github.com/moodle/moodle
   - Licencia: GNU GPL v3

### Microsoft Teams / Graph API

**Documentación Oficial:**

1. **Microsoft Graph API Documentation**
   - URL: https://docs.microsoft.com/graph/api/overview
   - Descripción: Documentación completa de Graph API

2. **Azure Active Directory Documentation**
   - URL: https://docs.microsoft.com/azure/active-directory/
   - Descripción: Gestión de identidades y acceso

3. **Microsoft Teams Developer Documentation**
   - URL: https://docs.microsoft.com/microsoftteams/platform/
   - Descripción: Desarrollo de aplicaciones para Teams

**Guías de Integración:**

1. **Microsoft Graph API - User Management**
   - URL: https://docs.microsoft.com/graph/api/resources/user
   - Descripción: Gestión de usuarios mediante API

2. **OAuth 2.0 in Azure AD**
   - URL: https://docs.microsoft.com/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow
   - Descripción: Autenticación con Client Credentials Flow

### Celery

**Documentación Oficial:**

1. **Celery Documentation**
   - URL: https://docs.celeryproject.org/
   - Descripción: Documentación completa de Celery

2. **Celery Best Practices**
   - URL: https://docs.celeryproject.org/en/stable/userguide/tasks.html#tips-and-best-practices
   - Descripción: Mejores prácticas para usar Celery

**Repositorios:**

1. **Celery**
   - URL: https://github.com/celery/celery
   - Licencia: BSD 3-Clause

2. **django-celery-beat**
   - URL: https://github.com/celery/django-celery-beat
   - Licencia: BSD 3-Clause

**Artículos Técnicos:**

1. Solem, A. (2009). *Celery: Distributed Task Queue.*
   - URL: https://celeryproject.org/

2. *Task Queue Architectures*
   - URL: https://www.cloudamqp.com/blog/part1-rabbitmq-best-practice.html
   - Descripción: Mejores prácticas en arquitecturas de colas

### Django

**Documentación Oficial:**

1. **Django Documentation**
   - URL: https://docs.djangoproject.com/
   - Descripción: Documentación completa de Django

2. **Django Admin Site**
   - URL: https://docs.djangoproject.com/en/stable/ref/contrib/admin/
   - Descripción: Personalización del panel de administración

**Libros:**

1. Greenfeld, D. R., & Roy, A. (2015). *Two Scoops of Django: Best Practices for Django 1.8.* Two Scoops Press.

2. Mele, A. (2016). *Django By Example.* Packt Publishing.

### Arquitectura de Software

**Libros:**

1. Fowler, M. (2002). *Patterns of Enterprise Application Architecture.* Addison-Wesley.

2. Newman, S. (2015). *Building Microservices: Designing Fine-Grained Systems.* O'Reilly Media.

3. Kleppmann, M. (2017). *Designing Data-Intensive Applications.* O'Reilly Media.

**Artículos:**

1. **Microservices Architecture Pattern**
   - URL: https://microservices.io/patterns/microservices.html
   - Descripción: Patrones de arquitectura de microservicios

2. **Service-Oriented Architecture**
   - URL: https://www.ibm.com/topics/soa
   - Descripción: Conceptos fundamentales de SOA

### Docker y Contenedores

**Documentación Oficial:**

1. **Docker Documentation**
   - URL: https://docs.docker.com/
   - Descripción: Documentación completa de Docker

2. **Docker Compose Documentation**
   - URL: https://docs.docker.com/compose/
   - Descripción: Orquestación de contenedores

**Repositorios:**

1. **Docker Engine**
   - URL: https://github.com/docker/docker
   - Licencia: Apache License 2.0

2. **Docker Compose**
   - URL: https://github.com/docker/compose
   - Licencia: Apache License 2.0

---

## Licencia y Contacto

**Licencia:** MIT License

**Copyright:** (c) 2025 Carlos Dagorret

**Institución:** Facultad de Ciencias Económicas, Universidad Nacional de Río Cuarto (UNRC)

**Repositorio:** https://github.com/[usuario]/lucy (público)

**Desarrollo:** https://github.com/[usuario]/pylucy (privado)

---

**Última Actualización:** Diciembre 2025
**Versión del Documento:** 1.0
