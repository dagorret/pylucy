--
-- PostgreSQL database dump
--

\restrict 6yeXVp1aDaRJk3eHgdwaGQSiHOhhWHticr3cWNZJkqWLueKE4DWKFkObNg4ycSZ

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
-- Name: cursos_cursoingreso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pylucy
--

SELECT pg_catalog.setval('public.cursos_cursoingreso_id_seq', 29, true);


--
-- PostgreSQL database dump complete
--

\unrestrict 6yeXVp1aDaRJk3eHgdwaGQSiHOhhWHticr3cWNZJkqWLueKE4DWKFkObNg4ycSZ

