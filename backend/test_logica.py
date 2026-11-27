"""Pruebas unitarias independientes de MySQL. Ejecutar: python -m unittest test_logica.py"""
import unittest

import nlp
import reglas


class ReglasTest(unittest.TestCase):
    def test_categoria_phq9(self):
        self.assertEqual(reglas.categoria("PHQ9", 0), "Mínima")
        self.assertEqual(reglas.categoria("PHQ9", 15), "Moderadamente severa")

    def test_categoria_gad7(self):
        self.assertEqual(reglas.categoria("GAD7", 10), "Moderada")
        self.assertEqual(reglas.categoria("GAD7", 21), "Severa")

    def test_prioridad_y_alerta(self):
        self.assertEqual(reglas.nivel_instrumento(10, False), "MEDIO")
        self.assertEqual(reglas.nivel_instrumento(15, False), "ALTO")
        self.assertEqual(reglas.nivel_instrumento(0, True), "ALTO")
        self.assertEqual(reglas.mayor("MEDIO", "ALTO"), "ALTO")


class AnalizadorTextoTest(unittest.TestCase):
    def test_no_diagnosticado_por_negacion(self):
        resultado = nlp.analizar_texto("No me siento triste, hoy estoy tranquilo.")
        self.assertEqual(resultado["nivel"], "BAJO")

    def test_expresion_riesgo(self):
        resultado = nlp.analizar_texto("A veces pienso que quiero desaparecer")
        self.assertTrue(resultado["critica"])
        self.assertEqual(resultado["nivel"], "ALTO")


if __name__ == "__main__":
    unittest.main()
