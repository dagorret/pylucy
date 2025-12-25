# Análisis de Lógica de Cursos de Ingreso

## Problema Identificado

Actualmente hay **múltiples cursos de ingreso** que aceptan las mismas carreras (LE, CP, LA):

| Curso | Nombre | Carreras | Modalidades | Comisiones |
|-------|--------|----------|-------------|------------|
| I3 | Ingreso Metodología | LE, CP, LA | PRES, DIST | 01, 02, 03, 1, 2, 3, 4, 5 |
| I4 | Ingreso Economía | LE, CP, LA | PRES, DIST | 01, 02, 03, 1, 2, 3, 4, 5 |
| I5 | Ingreso Administración | LE, CP, LA | PRES, DIST | 01, 02, 03, 1, 2, 3, 4, 5 |
| I6 | Ingreso Matemática | LE, CP, LA | PRES, DIST | 01, 02, 03, 1, 2, 3, 4, 5 |

## Escenario Actual

**Alumno:** Maitena Aguirre Godoy (ID 857)
- Carrera: CP (Contador Público)
- Modalidad: PRES (Presencial)
- Comisión: COMISION 2

**Cursos que coinciden:** I3, I4, I5, I6 (TODOS)

## Soluciones Posibles

### Opción 1: Enrollar en TODOS los cursos
```
Lógica: Un alumno de CP debe cursar TODAS las materias de ingreso
Resultado: Enrollar en I3, I4, I5, I6
Ventaja: El alumno tiene acceso a todas las materias que necesita
Desventaja: Puede ser abrumador si no debería ver todas desde el inicio
```

### Opción 2: Enrollar en UN SOLO curso (actual)
```
Lógica: Cada curso es independiente y el alumno se enrolla manualmente
Resultado: Enrollar solo en I5 (primero encontrado)
Ventaja: Simple
Desventaja: Puede no tener acceso a las otras materias necesarias
```

### Opción 3: Cursos específicos por carrera
```
Lógica: Cada carrera tiene sus propios cursos exclusivos
Cambio requerido: Modificar la configuración de cursos
- I3 solo para LE
- I4 solo para CP
- I5 solo para LA
etc.
Ventaja: Mapeo 1 a 1, sin ambigüedad
Desventaja: Si realmente comparten cursos, esto sería incorrecto
```

### Opción 4: Enrollamiento múltiple inteligente
```
Lógica: La función resolver_curso() devuelve LISTA de cursos
Cambio: Modificar resolver_curso() para devolver List[str]
Resultado: [I3, I4, I5, I6] para CP
Ventaja: Flexible, permite múltiples cursos
Desventaja: Necesita cambios en el código que llama a resolver_curso()
```

## Recomendación

Necesito que definas **cuál es la lógica correcta de negocio**:

1. ¿Un alumno de CP debe estar enrollado en I3, I4, I5 e I6 simultáneamente?
2. ¿O debe estar solo en uno específico?
3. ¿Los nombres de los cursos indican materias diferentes (Metodología, Economía, etc.)?

Si la respuesta es (1), implementaré **Opción 4**.
Si la respuesta es (2), necesito saber cómo decidir cuál curso específico.
Si la respuesta es (3), necesito más información sobre la lógica de negocio.
