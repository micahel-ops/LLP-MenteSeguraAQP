-- Datos minimos para ejecutar los scripts Python de demostracion.
-- Este archivo se puede ejecutar varias veces: no duplica los roles.
USE `sdtr`;

INSERT INTO rol (nombre, descripcion) VALUES
  ('ESTUDIANTE', 'Estudiante universitario'),
  ('PROFESIONAL', 'Profesional de salud mental'),
  ('ADMINISTRADOR', 'Administrador del sistema')
ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion);
