-- INSTALACION INICIAL: ejecutar solo en una base sdtr VACIA.
-- Para no borrar datos existentes, no repetir la importacion sobre una base en uso.
-- Los datos iniciales estan en seed.sql.
CREATE DATABASE IF NOT EXISTS `sdtr` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `sdtr`;
-- MySQL dump 10.13  Distrib 26.7.0, for Win64 (x86_64)
--
-- Host: localhost    Database: sdtr
-- ------------------------------------------------------
-- Server version	26.7.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
--
-- Table structure for table `alerta`
--

DROP TABLE IF EXISTS `alerta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alerta` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `evaluacion_id` bigint unsigned NOT NULL,
  `profesional_id` bigint unsigned DEFAULT NULL,
  `prioridad` decimal(6,2) NOT NULL,
  `motivo` varchar(200) NOT NULL,
  `estado` varchar(12) NOT NULL DEFAULT 'NUEVA',
  `creada_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `actualizada_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_alerta_evaluacion` (`evaluacion_id`),
  KEY `fk_alerta_profesional` (`profesional_id`),
  KEY `ix_alerta_estado_prioridad` (`estado`,`prioridad` DESC),
  CONSTRAINT `fk_alerta_evaluacion` FOREIGN KEY (`evaluacion_id`) REFERENCES `evaluacion` (`id`),
  CONSTRAINT `fk_alerta_profesional` FOREIGN KEY (`profesional_id`) REFERENCES `profesional` (`id`),
  CONSTRAINT `ck_alerta_estado` CHECK ((`estado` in (_utf8mb4'NUEVA',_utf8mb4'EN_REVISION',_utf8mb4'ATENDIDA',_utf8mb4'DESCARTADA'))),
  CONSTRAINT `ck_alerta_prioridad` CHECK ((`prioridad` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `analisis_nlp`
--

DROP TABLE IF EXISTS `analisis_nlp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `analisis_nlp` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `respuesta_id` bigint unsigned NOT NULL,
  `modelo_id` int unsigned NOT NULL,
  `nivel_riesgo` varchar(5) NOT NULL,
  `probabilidad` decimal(5,4) NOT NULL,
  `creado_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_analisis_respuesta` (`respuesta_id`),
  KEY `fk_analisis_modelo` (`modelo_id`),
  CONSTRAINT `fk_analisis_modelo` FOREIGN KEY (`modelo_id`) REFERENCES `modelo_nlp_version` (`id`),
  CONSTRAINT `fk_analisis_respuesta` FOREIGN KEY (`respuesta_id`) REFERENCES `respuesta` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_analisis_nivel` CHECK ((`nivel_riesgo` in (_utf8mb4'BAJO',_utf8mb4'MEDIO',_utf8mb4'ALTO'))),
  CONSTRAINT `ck_analisis_prob` CHECK ((`probabilidad` between 0 and 1))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dato_externo`
--

DROP TABLE IF EXISTS `dato_externo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dato_externo` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `fuente_id` smallint unsigned NOT NULL,
  `ejecucion_id` bigint unsigned NOT NULL,
  `indicador` varchar(150) NOT NULL,
  `ambito` varchar(100) NOT NULL DEFAULT 'Arequipa',
  `periodo` date NOT NULL,
  `valor` decimal(18,4) NOT NULL,
  `unidad` varchar(40) DEFAULT NULL,
  `procedencia_url` varchar(400) DEFAULT NULL,
  `actualizado_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dato_externo` (`fuente_id`,`indicador`,`ambito`,`periodo`),
  KEY `fk_dato_ejecucion` (`ejecucion_id`),
  KEY `ix_dato_externo_periodo` (`indicador`,`periodo`),
  CONSTRAINT `fk_dato_ejecucion` FOREIGN KEY (`ejecucion_id`) REFERENCES `ejecucion_fuente` (`id`),
  CONSTRAINT `fk_dato_fuente` FOREIGN KEY (`fuente_id`) REFERENCES `fuente_externa` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ejecucion_fuente`
--

DROP TABLE IF EXISTS `ejecucion_fuente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ejecucion_fuente` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `fuente_id` smallint unsigned NOT NULL,
  `inicio` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fin` datetime DEFAULT NULL,
  `estado` varchar(10) NOT NULL DEFAULT 'EN_CURSO',
  `registros_leidos` int DEFAULT NULL,
  `registros_validos` int DEFAULT NULL,
  `mensaje_error` text,
  PRIMARY KEY (`id`),
  KEY `ix_ejecucion_fuente` (`fuente_id`,`inicio` DESC),
  CONSTRAINT `fk_ejecucion_fuente` FOREIGN KEY (`fuente_id`) REFERENCES `fuente_externa` (`id`),
  CONSTRAINT `ck_ejecucion_estado` CHECK ((`estado` in (_utf8mb4'EN_CURSO',_utf8mb4'CORRECTA',_utf8mb4'CON_ERROR'))),
  CONSTRAINT `ck_ejecucion_fechas` CHECK (((`fin` is null) or (`fin` >= `inicio`))),
  CONSTRAINT `ck_ejecucion_leidos` CHECK (((`registros_leidos` is null) or (`registros_leidos` >= 0))),
  CONSTRAINT `ck_ejecucion_validos` CHECK (((`registros_validos` is null) or (`registros_validos` >= 0)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `estudiante`
--

DROP TABLE IF EXISTS `estudiante`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `estudiante` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint unsigned NOT NULL,
  `facultad_id` smallint unsigned NOT NULL,
  `codigo` varchar(20) NOT NULL,
  `ciclo` smallint DEFAULT NULL,
  `consentimiento_aceptado` tinyint(1) NOT NULL DEFAULT '0',
  `fecha_consentimiento` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_estudiante_usuario` (`usuario_id`),
  UNIQUE KEY `uq_estudiante_codigo` (`codigo`),
  KEY `fk_estudiante_facultad` (`facultad_id`),
  CONSTRAINT `fk_estudiante_facultad` FOREIGN KEY (`facultad_id`) REFERENCES `facultad` (`id`),
  CONSTRAINT `fk_estudiante_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`),
  CONSTRAINT `ck_consentimiento` CHECK (((0 = `consentimiento_aceptado`) or (`fecha_consentimiento` is not null))),
  CONSTRAINT `ck_estudiante_ciclo` CHECK (((`ciclo` is null) or (`ciclo` between 1 and 12)))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `evaluacion`
--

DROP TABLE IF EXISTS `evaluacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `evaluacion` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `estudiante_id` bigint unsigned NOT NULL,
  `instrumento_id` smallint unsigned NOT NULL,
  `modelo_id` int unsigned DEFAULT NULL,
  `fecha` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `puntaje_instrumento` smallint DEFAULT NULL,
  `categoria_instrumento` varchar(40) DEFAULT NULL,
  `puntaje_nlp` decimal(5,4) DEFAULT NULL,
  `nivel_riesgo` varchar(5) DEFAULT NULL,
  `prioridad` decimal(6,2) DEFAULT NULL,
  `variacion_riesgo` smallint DEFAULT NULL,
  `estado` varchar(10) NOT NULL DEFAULT 'ENVIADA',
  PRIMARY KEY (`id`),
  KEY `fk_evaluacion_instrumento` (`instrumento_id`),
  KEY `fk_evaluacion_modelo` (`modelo_id`),
  KEY `ix_evaluacion_estudiante_fecha` (`estudiante_id`,`fecha` DESC),
  KEY `ix_evaluacion_fecha` (`fecha`),
  KEY `ix_evaluacion_nivel` (`nivel_riesgo`),
  CONSTRAINT `fk_evaluacion_estudiante` FOREIGN KEY (`estudiante_id`) REFERENCES `estudiante` (`id`),
  CONSTRAINT `fk_evaluacion_instrumento` FOREIGN KEY (`instrumento_id`) REFERENCES `instrumento` (`id`),
  CONSTRAINT `fk_evaluacion_modelo` FOREIGN KEY (`modelo_id`) REFERENCES `modelo_nlp_version` (`id`),
  CONSTRAINT `ck_evaluacion_estado` CHECK ((`estado` in (_utf8mb4'ENVIADA',_utf8mb4'ANALIZADA',_utf8mb4'CERRADA'))),
  CONSTRAINT `ck_evaluacion_nivel` CHECK (((`nivel_riesgo` is null) or (`nivel_riesgo` in (_utf8mb4'BAJO',_utf8mb4'MEDIO',_utf8mb4'ALTO')))),
  CONSTRAINT `ck_evaluacion_nlp` CHECK (((`puntaje_nlp` is null) or (`puntaje_nlp` between 0 and 1))),
  CONSTRAINT `ck_evaluacion_prioridad` CHECK (((`prioridad` is null) or (`prioridad` >= 0))),
  CONSTRAINT `ck_evaluacion_puntaje` CHECK (((`puntaje_instrumento` is null) or (`puntaje_instrumento` >= 0)))
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `facultad`
--

DROP TABLE IF EXISTS `facultad`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `facultad` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `universidad_id` smallint unsigned NOT NULL,
  `nombre` varchar(120) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_facultad` (`universidad_id`,`nombre`),
  CONSTRAINT `fk_facultad_universidad` FOREIGN KEY (`universidad_id`) REFERENCES `universidad` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fuente_externa`
--

DROP TABLE IF EXISTS `fuente_externa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fuente_externa` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(120) NOT NULL,
  `organismo_tipo` varchar(15) NOT NULL,
  `tipo_acceso` varchar(5) NOT NULL,
  `clasificacion` varchar(13) NOT NULL,
  `url` varchar(400) NOT NULL,
  `frecuencia_dias` smallint NOT NULL DEFAULT '7',
  `activa` tinyint(1) NOT NULL DEFAULT '1',
  `ultima_actualizacion` datetime DEFAULT NULL,
  `creada_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_fuente_nombre` (`nombre`),
  CONSTRAINT `ck_fuente_acceso` CHECK ((`tipo_acceso` in (_utf8mb4'API',_utf8mb4'CSV',_utf8mb4'WEB',_utf8mb4'PDF'))),
  CONSTRAINT `ck_fuente_clasificacion` CHECK ((`clasificacion` in (_utf8mb4'RELACIONAL',_utf8mb4'NO_RELACIONAL'))),
  CONSTRAINT `ck_fuente_frecuencia` CHECK ((`frecuencia_dias` > 0)),
  CONSTRAINT `ck_fuente_organismo` CHECK ((`organismo_tipo` in (_utf8mb4'ESTADO',_utf8mb4'ONG',_utf8mb4'INTERNACIONAL')))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `instrumento`
--

DROP TABLE IF EXISTS `instrumento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `instrumento` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `codigo` varchar(20) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `tipo` varchar(20) NOT NULL,
  `version` varchar(20) NOT NULL DEFAULT '1.0',
  `puntaje_maximo` smallint NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_instrumento_codigo` (`codigo`),
  CONSTRAINT `ck_instrumento_puntaje` CHECK ((`puntaje_maximo` > 0)),
  CONSTRAINT `ck_instrumento_tipo` CHECK ((`tipo` in (_utf8mb4'DEPRESION',_utf8mb4'ANSIEDAD')))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `modelo_nlp_version`
--

DROP TABLE IF EXISTS `modelo_nlp_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `modelo_nlp_version` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `version` varchar(20) NOT NULL,
  `estado` varchar(12) NOT NULL DEFAULT 'CANDIDATA',
  `precision_modelo` decimal(5,4) DEFAULT NULL,
  `recall_modelo` decimal(5,4) DEFAULT NULL,
  `f1_modelo` decimal(5,4) DEFAULT NULL,
  `casos_entrenamiento` int DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `publicado_en` datetime DEFAULT NULL,
  `aprobado_por` bigint unsigned DEFAULT NULL,
  `motivo_decision` text,
  `vigente` tinyint GENERATED ALWAYS AS (if((`estado` = _utf8mb4'VIGENTE'),1,NULL)) STORED,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_modelo_version` (`version`),
  UNIQUE KEY `ux_modelo_vigente` (`vigente`),
  KEY `fk_modelo_aprobador` (`aprobado_por`),
  CONSTRAINT `fk_modelo_aprobador` FOREIGN KEY (`aprobado_por`) REFERENCES `usuario` (`id`),
  CONSTRAINT `ck_modelo_casos` CHECK (((`casos_entrenamiento` is null) or (`casos_entrenamiento` >= 0))),
  CONSTRAINT `ck_modelo_estado` CHECK ((`estado` in (_utf8mb4'CANDIDATA',_utf8mb4'VIGENTE',_utf8mb4'RECHAZADA',_utf8mb4'RETIRADA'))),
  CONSTRAINT `ck_modelo_f1` CHECK (((`f1_modelo` is null) or (`f1_modelo` between 0 and 1))),
  CONSTRAINT `ck_modelo_precision` CHECK (((`precision_modelo` is null) or (`precision_modelo` between 0 and 1))),
  CONSTRAINT `ck_modelo_recall` CHECK (((`recall_modelo` is null) or (`recall_modelo` between 0 and 1)))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notificacion`
--

DROP TABLE IF EXISTS `notificacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notificacion` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint unsigned NOT NULL,
  `alerta_id` bigint unsigned DEFAULT NULL,
  `tipo` varchar(30) NOT NULL,
  `mensaje` varchar(300) NOT NULL,
  `leida` tinyint(1) NOT NULL DEFAULT '0',
  `creada_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_notif_alerta` (`alerta_id`),
  KEY `ix_notificacion_usuario` (`usuario_id`,`leida`),
  CONSTRAINT `fk_notif_alerta` FOREIGN KEY (`alerta_id`) REFERENCES `alerta` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_notif_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `opcion_respuesta`
--

DROP TABLE IF EXISTS `opcion_respuesta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `opcion_respuesta` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `pregunta_id` int unsigned NOT NULL,
  `texto` varchar(200) NOT NULL,
  `puntaje` smallint NOT NULL,
  `orden` smallint NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `fk_opcion_pregunta` (`pregunta_id`),
  CONSTRAINT `fk_opcion_pregunta` FOREIGN KEY (`pregunta_id`) REFERENCES `pregunta` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=65 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pregunta`
--

DROP TABLE IF EXISTS `pregunta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pregunta` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `instrumento_id` smallint unsigned NOT NULL,
  `numero` smallint NOT NULL,
  `enunciado` text NOT NULL,
  `tipo` varchar(10) NOT NULL,
  `obligatoria` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_pregunta` (`instrumento_id`,`numero`),
  CONSTRAINT `fk_pregunta_instrumento` FOREIGN KEY (`instrumento_id`) REFERENCES `instrumento` (`id`),
  CONSTRAINT `ck_pregunta_numero` CHECK ((`numero` > 0)),
  CONSTRAINT `ck_pregunta_tipo` CHECK ((`tipo` in (_utf8mb4'CERRADA',_utf8mb4'ABIERTA')))
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `profesional`
--

DROP TABLE IF EXISTS `profesional`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `profesional` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint unsigned NOT NULL,
  `numero_colegiatura` varchar(20) DEFAULT NULL,
  `especialidad` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_profesional_usuario` (`usuario_id`),
  UNIQUE KEY `uq_profesional_colegiatura` (`numero_colegiatura`),
  CONSTRAINT `fk_profesional_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `profesional_facultad`
--

DROP TABLE IF EXISTS `profesional_facultad`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `profesional_facultad` (
  `profesional_id` bigint unsigned NOT NULL,
  `facultad_id` smallint unsigned NOT NULL,
  PRIMARY KEY (`profesional_id`,`facultad_id`),
  KEY `fk_pf_facultad` (`facultad_id`),
  CONSTRAINT `fk_pf_facultad` FOREIGN KEY (`facultad_id`) REFERENCES `facultad` (`id`),
  CONSTRAINT `fk_pf_profesional` FOREIGN KEY (`profesional_id`) REFERENCES `profesional` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `proyeccion_tendencia`
--

DROP TABLE IF EXISTS `proyeccion_tendencia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `proyeccion_tendencia` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `facultad_id` smallint unsigned DEFAULT NULL,
  `periodo` date NOT NULL,
  `evaluaciones_proyectadas` int NOT NULL,
  `metodo` varchar(50) NOT NULL DEFAULT 'TENDENCIA_LINEAL',
  `generada_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_proyeccion_facultad` (`facultad_id`),
  CONSTRAINT `fk_proyeccion_facultad` FOREIGN KEY (`facultad_id`) REFERENCES `facultad` (`id`),
  CONSTRAINT `ck_proyeccion_valor` CHECK ((`evaluaciones_proyectadas` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `recomendacion`
--

DROP TABLE IF EXISTS `recomendacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recomendacion` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `nivel_riesgo` varchar(5) NOT NULL,
  `titulo` varchar(150) NOT NULL,
  `descripcion` text NOT NULL,
  `recurso_url` varchar(300) DEFAULT NULL,
  `activa` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  CONSTRAINT `ck_recomendacion_nivel` CHECK ((`nivel_riesgo` in (_utf8mb4'BAJO',_utf8mb4'MEDIO',_utf8mb4'ALTO')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reevaluacion`
--

DROP TABLE IF EXISTS `reevaluacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reevaluacion` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `estudiante_id` bigint unsigned NOT NULL,
  `evaluacion_origen_id` bigint unsigned NOT NULL,
  `fecha_programada` date NOT NULL,
  `estado` varchar(10) NOT NULL DEFAULT 'PENDIENTE',
  `recordatorio_enviado` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `fk_reeval_estudiante` (`estudiante_id`),
  KEY `fk_reeval_evaluacion` (`evaluacion_origen_id`),
  KEY `ix_reevaluacion_fecha` (`fecha_programada`,`estado`),
  CONSTRAINT `fk_reeval_estudiante` FOREIGN KEY (`estudiante_id`) REFERENCES `estudiante` (`id`),
  CONSTRAINT `fk_reeval_evaluacion` FOREIGN KEY (`evaluacion_origen_id`) REFERENCES `evaluacion` (`id`),
  CONSTRAINT `ck_reeval_estado` CHECK ((`estado` in (_utf8mb4'PENDIENTE',_utf8mb4'REALIZADA',_utf8mb4'VENCIDA',_utf8mb4'CANCELADA')))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `registro_actividad`
--

DROP TABLE IF EXISTS `registro_actividad`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `registro_actividad` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint unsigned DEFAULT NULL,
  `accion` varchar(60) NOT NULL,
  `entidad` varchar(60) DEFAULT NULL,
  `entidad_id` bigint unsigned DEFAULT NULL,
  `detalle` json DEFAULT NULL,
  `ip` varchar(45) DEFAULT NULL,
  `fecha` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_actividad_usuario` (`usuario_id`),
  KEY `ix_actividad_fecha` (`fecha` DESC),
  CONSTRAINT `fk_actividad_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=174 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50003 TRIGGER `tg_actividad_no_update` BEFORE UPDATE ON `registro_actividad` FOR EACH ROW BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'registro_actividad es de solo inserción';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50003 TRIGGER `tg_actividad_no_delete` BEFORE DELETE ON `registro_actividad` FOR EACH ROW BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'registro_actividad es de solo inserción';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `reporte_generado`
--

DROP TABLE IF EXISTS `reporte_generado`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reporte_generado` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `tipo` varchar(40) NOT NULL,
  `formato` varchar(5) NOT NULL,
  `filtros` json NOT NULL DEFAULT (json_object()),
  `generado_por` bigint unsigned NOT NULL,
  `generado_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_reporte_usuario` (`generado_por`),
  CONSTRAINT `fk_reporte_usuario` FOREIGN KEY (`generado_por`) REFERENCES `usuario` (`id`),
  CONSTRAINT `ck_reporte_formato` CHECK ((`formato` in (_utf8mb4'PDF',_utf8mb4'XLSX')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `respuesta`
--

DROP TABLE IF EXISTS `respuesta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `respuesta` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `evaluacion_id` bigint unsigned NOT NULL,
  `pregunta_id` int unsigned NOT NULL,
  `opcion_id` int unsigned DEFAULT NULL,
  `valor_numerico` smallint DEFAULT NULL,
  `texto_libre` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_respuesta` (`evaluacion_id`,`pregunta_id`),
  KEY `fk_respuesta_pregunta` (`pregunta_id`),
  KEY `fk_respuesta_opcion` (`opcion_id`),
  CONSTRAINT `fk_respuesta_evaluacion` FOREIGN KEY (`evaluacion_id`) REFERENCES `evaluacion` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_respuesta_opcion` FOREIGN KEY (`opcion_id`) REFERENCES `opcion_respuesta` (`id`),
  CONSTRAINT `fk_respuesta_pregunta` FOREIGN KEY (`pregunta_id`) REFERENCES `pregunta` (`id`),
  CONSTRAINT `ck_respuesta_contenido` CHECK (((`opcion_id` is not null) or (`valor_numerico` is not null) or (`texto_libre` is not null)))
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rol`
--

DROP TABLE IF EXISTS `rol`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rol` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `descripcion` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_rol_nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `seguimiento`
--

DROP TABLE IF EXISTS `seguimiento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seguimiento` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `alerta_id` bigint unsigned NOT NULL,
  `profesional_id` bigint unsigned NOT NULL,
  `fecha` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `descripcion` text NOT NULL,
  `estado_resultante` varchar(12) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_seguimiento_alerta` (`alerta_id`),
  KEY `fk_seguimiento_profesional` (`profesional_id`),
  CONSTRAINT `fk_seguimiento_alerta` FOREIGN KEY (`alerta_id`) REFERENCES `alerta` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_seguimiento_profesional` FOREIGN KEY (`profesional_id`) REFERENCES `profesional` (`id`),
  CONSTRAINT `ck_seguimiento_estado` CHECK ((`estado_resultante` in (_utf8mb4'EN_REVISION',_utf8mb4'ATENDIDA',_utf8mb4'DESCARTADA')))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `termino_influyente`
--

DROP TABLE IF EXISTS `termino_influyente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `termino_influyente` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `analisis_id` bigint unsigned NOT NULL,
  `termino` varchar(80) NOT NULL,
  `peso` decimal(6,4) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_termino_analisis` (`analisis_id`),
  CONSTRAINT `fk_termino_analisis` FOREIGN KEY (`analisis_id`) REFERENCES `analisis_nlp` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `universidad`
--

DROP TABLE IF EXISTS `universidad`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `universidad` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(150) NOT NULL,
  `ciudad` varchar(80) NOT NULL DEFAULT 'Arequipa',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_universidad_nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `rol_id` smallint unsigned NOT NULL,
  `correo` varchar(150) NOT NULL,
  `contrasena_hash` varchar(255) NOT NULL,
  `nombres` varchar(100) NOT NULL,
  `apellidos` varchar(100) NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `intentos_fallidos` smallint NOT NULL DEFAULT '0',
  `bloqueado_hasta` datetime DEFAULT NULL,
  `ultimo_acceso` datetime DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_usuario_correo` (`correo`),
  KEY `fk_usuario_rol` (`rol_id`),
  CONSTRAINT `fk_usuario_rol` FOREIGN KEY (`rol_id`) REFERENCES `rol` (`id`),
  CONSTRAINT `ck_usuario_correo` CHECK ((`correo` like _utf8mb4'%_@_%')),
  CONSTRAINT `ck_usuario_intentos` CHECK ((`intentos_fallidos` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary view structure for view `v_riesgo_por_facultad`
--

DROP TABLE IF EXISTS `v_riesgo_por_facultad`;
/*!50001 DROP VIEW IF EXISTS `v_riesgo_por_facultad`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_riesgo_por_facultad` AS SELECT 
 1 AS `facultad_id`,
 1 AS `facultad`,
 1 AS `mes`,
 1 AS `evaluaciones`,
 1 AS `riesgo_bajo`,
 1 AS `riesgo_medio`,
 1 AS `riesgo_alto`,
 1 AS `alertas`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `validacion_alerta`
--

DROP TABLE IF EXISTS `validacion_alerta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `validacion_alerta` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `alerta_id` bigint unsigned NOT NULL,
  `profesional_id` bigint unsigned NOT NULL,
  `confirma_riesgo` tinyint(1) NOT NULL,
  `justificacion` text NOT NULL,
  `apta_entrenamiento` tinyint(1) NOT NULL DEFAULT '1',
  `fecha` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_validacion_alerta` (`alerta_id`),
  KEY `fk_validacion_profesional` (`profesional_id`),
  CONSTRAINT `fk_validacion_alerta` FOREIGN KEY (`alerta_id`) REFERENCES `alerta` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_validacion_profesional` FOREIGN KEY (`profesional_id`) REFERENCES `profesional` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping events for database 'sdtr'
--

--
-- Dumping routines for database 'sdtr'
--

--
-- Final view structure for view `v_riesgo_por_facultad`
--

/*!50001 DROP VIEW IF EXISTS `v_riesgo_por_facultad`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 SQL SECURITY INVOKER */
/*!50001 VIEW `v_riesgo_por_facultad` AS select `f`.`id` AS `facultad_id`,`f`.`nombre` AS `facultad`,cast(date_format(`e`.`fecha`,'%Y-%m-01') as date) AS `mes`,count(`e`.`id`) AS `evaluaciones`,sum((case when (`e`.`nivel_riesgo` = 'BAJO') then 1 else 0 end)) AS `riesgo_bajo`,sum((case when (`e`.`nivel_riesgo` = 'MEDIO') then 1 else 0 end)) AS `riesgo_medio`,sum((case when (`e`.`nivel_riesgo` = 'ALTO') then 1 else 0 end)) AS `riesgo_alto`,count(distinct `a`.`id`) AS `alertas` from (((`evaluacion` `e` join `estudiante` `s` on((`s`.`id` = `e`.`estudiante_id`))) join `facultad` `f` on((`f`.`id` = `s`.`facultad_id`))) left join `alerta` `a` on((`a`.`evaluacion_id` = `e`.`id`))) group by `f`.`id`,`f`.`nombre`,cast(date_format(`e`.`fecha`,'%Y-%m-01') as date) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-26 18:20:57
