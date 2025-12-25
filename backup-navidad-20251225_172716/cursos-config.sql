--
-- PostgreSQL database dump
--

\restrict Z0Pak0bFozCSotkm3b42qTIDcHvCDpcqvOSgbW1z6QbjtqiMKMGcZYCJf2DxAi8

-- Dumped from database version 16.11 (Debian 16.11-1.pgdg13+1)
-- Dumped by pg_dump version 16.11 (Debian 16.11-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: alumnos_configuracion; Type: TABLE DATA; Schema: public; Owner: pylucy
--

INSERT INTO public.alumnos_configuracion (id, preinscriptos_frecuencia_segundos, aspirantes_frecuencia_segundos, ingresantes_frecuencia_segundos, teams_tenant_id, teams_client_id, teams_client_secret, moodle_base_url, moodle_wstoken, actualizado_en, actualizado_por, preinscriptos_dia_inicio, preinscriptos_dia_fin, aspirantes_dia_inicio, aspirantes_dia_fin, ingresantes_dia_inicio, ingresantes_dia_fin, batch_size, rate_limit_moodle, rate_limit_teams, email_from, email_host, email_port, email_use_tls, account_prefix, moodle_email_type, moodle_student_roleid, sial_base_url, sial_basic_pass, sial_basic_user, email_plantilla_bienvenida, email_plantilla_credenciales, email_plantilla_password, moodle_auth_method, rate_limit_uti, email_asunto_bienvenida, email_asunto_credenciales, email_asunto_password, email_asunto_enrollamiento, email_plantilla_enrollamiento, aspirantes_enviar_email, ingresantes_enviar_email, preinscriptos_enviar_email, moodle_courses_config) VALUES (1, 3600, 3600, 3600, '1f7d4699-ccd7-45d6-bc78-b8b950bcaedc', '138e98af-33e5-439c-9981-3caaedc65c70', 'VE~8Q~SbnnIUg-iEHnr1m8nxu5J0RAskpLJPlbuU', 'https://v.eco.unrc.edu.ar', '45fba879dcddc17a16436ac156cb880e', '2025-12-13 21:03:26.330414+00', '', NULL, NULL, NULL, NULL, NULL, NULL, 20, 30, 10, 'no-reply@eco.unrc.edu.ar', 'mailhog', 1025, false, 'test-a', 'institucional', 5, 'https://sisinfo.unrc.edu.ar', 'pos15MAL@kapri', 'SIAL04_565', '
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #0066cc; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>¡Bienvenido/a a la Facultad de Ciencias Económicas!</h1>
        </div>
        <div class="content">
            <p>Estimado/a <strong>{apellido}, {nombre}</strong> (DNI: {dni}):</p>

            <p>Es un placer darte la bienvenida a la <strong>Facultad de Ciencias Económicas de la UNRC</strong>.</p>

            <p>Hemos recibido tu inscripción correctamente. En los próximos días recibirás información sobre:</p>
            <ul>
                <li>Credenciales de acceso a Microsoft Teams</li>
                <li>Acceso al campus virtual (Moodle)</li>
                <li>Información sobre el curso de ingreso</li>
                <li>Calendario académico</li>
            </ul>

            <p>Cualquier consulta, no dudes en contactarnos a: <a href="mailto:economia@eco.unrc.edu.ar">economia@eco.unrc.edu.ar</a></p>

            <p>¡Bienvenido/a y éxitos en esta nueva etapa!</p>
        </div>
        <div class="footer">
            <p>Facultad de Ciencias Económicas - UNRC<br>
            Ruta Nacional 36 Km 601 - Río Cuarto, Córdoba<br>
            <a href="https://eco.unrc.edu.ar">www.eco.unrc.edu.ar</a></p>
        </div>
    </div>
</body>
</html>
', '
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .credentials {{ background-color: white; padding: 15px; margin: 20px 0; border-left: 4px solid #28a745; }}
        .credentials strong {{ color: #28a745; }}
        .warning {{ background-color: #fff3cd; padding: 10px; margin: 15px 0; border-left: 4px solid #ffc107; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Credenciales de Acceso - Microsoft Teams</h1>
        </div>
        <div class="content">
            <p>Estimado/a <strong>{apellido}, {nombre}</strong>:</p>

            <p>Tu cuenta de <strong>Microsoft Teams</strong> ha sido creada exitosamente. A continuación encontrarás tus credenciales de acceso:</p>

            <div class="credentials">
                <p><strong>Usuario (UPN):</strong> {upn}</p>
                <p><strong>Contraseña temporal:</strong> {password}</p>
            </div>

            <div class="warning">
                <p><strong>⚠️ IMPORTANTE:</strong></p>
                <ul>
                    <li>Esta es una contraseña <strong>temporal</strong></li>
                    <li>Se te pedirá cambiarla en tu primer inicio de sesión</li>
                    <li>Guarda bien tu nueva contraseña</li>
                    <li>No compartas tus credenciales con nadie</li>
                </ul>
            </div>

            <h3>¿Cómo acceder?</h3>
            <ol>
                <li>Ingresa a <a href="https://teams.microsoft.com">teams.microsoft.com</a></li>
                <li>Usa tu usuario (UPN) y contraseña temporal</li>
                <li>Sigue las instrucciones para cambiar tu contraseña</li>
                <li>¡Listo! Ya podés acceder a tus clases y materiales</li>
            </ol>

            <p>También podés descargar la aplicación de Teams para escritorio o móvil desde:</p>
            <p><a href="https://www.microsoft.com/es-ar/microsoft-teams/download-app">Descargar Microsoft Teams</a></p>

            <p>Cualquier problema con tu acceso, contactanos a: <a href="mailto:soporte@eco.unrc.edu.ar">soporte@eco.unrc.edu.ar</a></p>
        </div>
        <div class="footer">
            <p>Facultad de Ciencias Económicas - UNRC<br>
            Ruta Nacional 36 Km 601 - Río Cuarto, Córdoba<br>
            <a href="https://eco.unrc.edu.ar">www.eco.unrc.edu.ar</a></p>
        </div>
    </div>
</body>
</html>
', '
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #ffc107; color: #333; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .credentials {{ background-color: white; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107; }}
        .credentials strong {{ color: #ffc107; }}
        .warning {{ background-color: #f8d7da; padding: 10px; margin: 15px 0; border-left: 4px solid #dc3545; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Reseteo de Contraseña - Microsoft Teams</h1>
        </div>
        <div class="content">
            <p>Estimado/a <strong>{apellido}, {nombre}</strong>:</p>

            <p>Tu contraseña de <strong>Microsoft Teams</strong> ha sido reseteada.</p>

            <div class="credentials">
                <p><strong>Usuario (UPN):</strong> {upn}</p>
                <p><strong>Nueva contraseña temporal:</strong> {password}</p>
            </div>

            <div class="warning">
                <p><strong>⚠️ ATENCIÓN:</strong></p>
                <ul>
                    <li>Esta contraseña <strong>reemplaza</strong> tu contraseña anterior</li>
                    <li>Es una contraseña <strong>temporal</strong></li>
                    <li>Deberás cambiarla en tu próximo inicio de sesión</li>
                    <li>Si no solicitaste este cambio, contacta inmediatamente a soporte</li>
                </ul>
            </div>

            <h3>Pasos para acceder:</h3>
            <ol>
                <li>Ve a <a href="https://teams.microsoft.com">teams.microsoft.com</a></li>
                <li>Ingresa con tu usuario y la nueva contraseña temporal</li>
                <li>Cambia tu contraseña cuando se te solicite</li>
            </ol>

            <p>Si tenés problemas para acceder, escribinos a: <a href="mailto:soporte@eco.unrc.edu.ar">soporte@eco.unrc.edu.ar</a></p>
        </div>
        <div class="footer">
            <p>Facultad de Ciencias Económicas - UNRC<br>
            Ruta Nacional 36 Km 601 - Río Cuarto, Córdoba<br>
            <a href="https://eco.unrc.edu.ar">www.eco.unrc.edu.ar</a></p>
        </div>
    </div>
</body>
</html>
', 'oidc', 60, 'Bienvenido/a a la UNRC', 'Credenciales de acceso - UNRC', 'Nueva contraseña - UNRC', 'Acceso al Ecosistema Virtual - UNRC', '', true, true, true, '{}');


--
-- Data for Name: cursos_cursoingreso; Type: TABLE DATA; Schema: public; Owner: pylucy
--

INSERT INTO public.cursos_cursoingreso (id, nombre, curso_moodle, carreras, activo, modalidades, comisiones) VALUES (20, 'Ingreso Administración', 'I5', '["LE", "CP", "LA"]', true, '["PRES", "DIST"]', '["COMISION 01", "COMISION 02", "COMISION 03", "COMISION 1", "COMISION 2", "COMISION 3", "COMISION 4", "COMISION 5"]');
INSERT INTO public.cursos_cursoingreso (id, nombre, curso_moodle, carreras, activo, modalidades, comisiones) VALUES (22, 'Ingreso Contabilidad (Cát 3)', 'I2', '["LE", "CP", "LA"]', true, '["DIST"]', '["COMISION 03"]');
INSERT INTO public.cursos_cursoingreso (id, nombre, curso_moodle, carreras, activo, modalidades, comisiones) VALUES (21, 'Ingreso Contabilidad (Cát 3)', 'I1', '["LE", "CP", "LA"]', true, '["DIST"]', '["COMISION 01", "COMISION 02"]');
INSERT INTO public.cursos_cursoingreso (id, nombre, curso_moodle, carreras, activo, modalidades, comisiones) VALUES (23, 'Ingreso Economía', 'I4', '["LE", "CP", "LA"]', true, '["PRES", "DIST"]', '["COMISION 01", "COMISION 02", "COMISION 03", "COMISION 1", "COMISION 2", "COMISION 3", "COMISION 4", "COMISION 5"]');
INSERT INTO public.cursos_cursoingreso (id, nombre, curso_moodle, carreras, activo, modalidades, comisiones) VALUES (24, 'Ingreso Matemática', 'I6', '["LE", "CP", "LA"]', true, '["PRES", "DIST"]', '["COMISION 01", "COMISION 02", "COMISION 03", "COMISION 1", "COMISION 2", "COMISION 3", "COMISION 4", "COMISION 5"]');
INSERT INTO public.cursos_cursoingreso (id, nombre, curso_moodle, carreras, activo, modalidades, comisiones) VALUES (25, 'Ingreso Metodología', 'I3', '["LE", "CP", "LA"]', true, '["PRES", "DIST"]', '["COMISION 01", "COMISION 02", "COMISION 03", "COMISION 1", "COMISION 2", "COMISION 3", "COMISION 4", "COMISION 5"]');
INSERT INTO public.cursos_cursoingreso (id, nombre, curso_moodle, carreras, activo, modalidades, comisiones) VALUES (26, 'Ingreso TGAA', 'I7', '["TGA"]', true, '["PRES"]', '["COMISION 1", "COMISION 2", "COMISION 3", "COMISION 4", "COMISION 5"]');
INSERT INTO public.cursos_cursoingreso (id, nombre, curso_moodle, carreras, activo, modalidades, comisiones) VALUES (27, 'Ingreso TGE', 'I8', '["TGE"]', true, '["PRES"]', '["COMISION 1", "COMISION 2", "COMISION 3", "COMISION 4", "COMISION 5"]');
INSERT INTO public.cursos_cursoingreso (id, nombre, curso_moodle, carreras, activo, modalidades, comisiones) VALUES (28, 'Ingreso Contabilidad (Cát 1 y 2)', 'I1', '["LE", "CP", "LA"]', true, '["PRES"]', '["COMISION 1", "COMISION 3", "COMISION 4"]');
INSERT INTO public.cursos_cursoingreso (id, nombre, curso_moodle, carreras, activo, modalidades, comisiones) VALUES (29, 'Ingreso Contabilidad (Cát 3)', 'I2', '["LE", "CP", "LA"]', true, '["PRES"]', '["COMISION 2", "COMISION 5"]');


--
-- Name: alumnos_configuracion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pylucy
--

SELECT pg_catalog.setval('public.alumnos_configuracion_id_seq', 1, true);


--
-- Name: cursos_cursoingreso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pylucy
--

SELECT pg_catalog.setval('public.cursos_cursoingreso_id_seq', 29, true);


--
-- PostgreSQL database dump complete
--

\unrestrict Z0Pak0bFozCSotkm3b42qTIDcHvCDpcqvOSgbW1z6QbjtqiMKMGcZYCJf2DxAi8

