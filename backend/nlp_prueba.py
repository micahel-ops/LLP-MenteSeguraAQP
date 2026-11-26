"""Prueba rápida del motor de texto desde la terminal.
Uso:  python nlp_prueba.py "Me siento muy cansado y sin ganas de estudiar"
"""
import sys

from nlp import analizar_texto

textos = sys.argv[1:] or [
    "Me siento bien y tranquilo, estoy disfrutando la universidad.",
    "Me siento muy cansado y sin ganas de estudiar, casi no duermo.",
    "Estoy muy triste, sin esperanza, me siento solo y no puedo más.",
    "No me siento triste, solo estoy un poco cansado.",
    "A veces pienso que quiero desaparecer.",
]
for t in textos:
    r = analizar_texto(t)
    print("\nTexto :", t)
    print("Nivel :", r["nivel"], "| intensidad:", r["probabilidad"], "| crítico:", r["critica"])
    print("Señales:", ", ".join(f"{x['termino']} ({x['peso']})" for x in r["terminos"]) or "ninguna")
