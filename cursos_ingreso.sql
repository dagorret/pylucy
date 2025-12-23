-- Datos de cursos de ingreso
INSERT INTO cursos_cursoingreso (id, nombre, curso_moodle, carreras, activo, modalidades, comisiones) VALUES
(7, 'Ingreso Contabilidad (Cát 3)', 'I2', '["LE", "CP", "LA"]', true, '["DIST"]', '["COMISION 03"]'),
(8, 'Ingreso Contabilidad (Cát 3)', 'I2', '["LE", "CP", "LA"]', true, '["PRES"]', '["COMISION 2", "COMISION 5"]'),
(5, 'Ingreso Contabilidad (Cát 1 y 2)', 'I1', '["LE", "CP", "LA"]', true, '["PRES"]', '["COMISION 1", "COMISION 3", "COMISION 4"]'),
(6, 'Ingreso Contabilidad (Cát 3)', 'I1', '["LE", "CP", "LA"]', true, '["DIST"]', '["COMISION 01", "COMISION 02"]'),
(9, 'Ingreso Metodología', 'I3', '["LE", "CP", "LA"]', true, '["PRES", "DIST"]', '["COMISION 01", "COMISION 02", "COMISION 03", "COMISION 1", "COMISION 2", "COMISION 3", "COMISION 4", "COMISION 5"]'),
(10, 'Ingreso Economía', 'I4', '["LE", "CP", "LA"]', true, '["PRES", "DIST"]', '["COMISION 01", "COMISION 02", "COMISION 03", "COMISION 1", "COMISION 2", "COMISION 3", "COMISION 4", "COMISION 5"]'),
(11, 'Ingreso Administración', 'I5', '["LE", "CP", "LA"]', true, '["PRES", "DIST"]', '["COMISION 01", "COMISION 02", "COMISION 03", "COMISION 1", "COMISION 2", "COMISION 3", "COMISION 4", "COMISION 5"]'),
(12, 'Ingreso Matemática', 'I6', '["LE", "CP", "LA"]', true, '["PRES", "DIST"]', '["COMISION 01", "COMISION 02", "COMISION 03", "COMISION 1", "COMISION 2", "COMISION 3", "COMISION 4", "COMISION 5"]'),
(13, 'Ingreso TGAA', 'I7', '["TGA"]', true, '["PRES"]', '["COMISION 1", "COMISION 2", "COMISION 3", "COMISION 4", "COMISION 5"]'),
(14, 'Ingreso TGE', 'I8', '["TGE"]', true, '["PRES"]', '["COMISION 1", "COMISION 2", "COMISION 3", "COMISION 4", "COMISION 5"]')
ON CONFLICT (id) DO NOTHING;

-- Actualizar secuencia
SELECT setval('cursos_cursoingreso_id_seq', 14, true);
