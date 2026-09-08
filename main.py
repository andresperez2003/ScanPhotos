"""Punto de entrada: extrae LOTE y fecha de vencimiento via OpenRouter
sobre el mismo lote de fotos (photos/1.jpeg .. photos/29.jpeg).

Cada proveedor vive en su propio archivo dentro de providers/ y expone una
unica funcion run(prompt) -> list[dict]. Aqui solo se define el prompt y se
llama a los proveedores configurados.
"""
from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from providers import openrouter

load_dotenv()

PROMPT = """Esta es la impresion (codificado / inkjet) de un empaque de alimentos.
Extrae el numero de LOTE y la FECHA DE VENCIMIENTO.

IDENTIFICAR LOS CAMPOS
- El vencimiento viene despues de VEN, VENC, VENCE, V. o CAD.
- El lote esta marcado por L, L., L:, LOTE o LOT.
- Si no hay marcador, el codigo alfanumerico que no sea una fecha es el lote.
- La L de unidades o palabras (500ML, CL, KL, NEUTRAL) no es marcador de lote.

LOTE: COPIA LITERAL, no lo limpies
- Devuelvelo EXACTAMENTE como esta impreso, incluyendo el marcador, las etiquetas,
  los espacios y los separadores. De limpiarlo se encarga otro proceso.
  Ej: "L61050467"         -> devuelve "L61050467"
  Ej: "L VEN 01 SEP 2026" -> devuelve "L VEN 01 SEP 2026"
  Ej: "LOTE 04-L1 0107"   -> devuelve "LOTE 04-L1 0107"
- Los dos puntos DENTRO del codigo (ej: L15616:34GMMP) son parte del lote: conservalos.
- Es valido que el lote sea identico a la fecha impresa (ej: "L VEN 01 SEP 2026",
  donde una sola impresion sirve para los dos campos). No lo descartes, no devuelvas
  null, y no inventes un lote distinto.

FECHA: descomponer, NO calcular
- "fecha_cruda": los caracteres tal como aparecen, sin interpretar.
- Descompon la fecha en venc_dia / venc_mes / venc_anio (numeros).
- Anio de 2 digitos -> 20XX. Si el dia y el mes son ambiguos, asume DD/MM
  (formato latinoamericano).
- Meses en letras: ENE=1 FEB=2 MAR=3 ABR=4 MAY=5 JUN=6 JUL=7 AGO=8 SEP=9
  OCT=10 NOV=11 DIC=12.
- Si el empaque trae dia, mes y anio -> venc_precision = "dia".
- Si el empaque SOLO trae mes y anio (ej: 05/2027, DIC/26, SEP 2026) ->
  venc_precision = "mes" y venc_dia = null. NO completes el dia:
  de eso se encarga otro proceso.
- Si no hay fecha legible -> venc_precision = "nulo" y los tres campos en null.

CUANDO NO LEES ALGO
- Devuelve null en ese campo y explica en "notas". NO adivines ni completes
  caracteres que no ves. Un null es preferible a un valor inventado.

CONFIANZA - usa estos disparadores, no tu impresion general
- "baja" OBLIGATORIO si: el codigo toca o se sale del borde de la imagen,
  hay caracteres tapados por brillo/pliegue/relieve, o dudas entre dos
  lecturas que dan valores distintos.
- "media" si: el valor es correcto pero algun caracter admite otra lectura
  (0/O, 1/I/L, 5/S, 8/B, 2/Z), o los separadores son ambiguos.
- "alta" solo si podrias transcribir el codigo de memoria sin volver a mirar."""

PROVIDERS = {
    "openrouter": openrouter.run,
}


def main() -> None:
    comparison: dict[str, object] = {}

    for name, run_fn in PROVIDERS.items():
        print(f"\n=== {name} ===")
        try:
            comparison[name] = run_fn(PROMPT)
        except Exception as e:
            print(f"[{name}] fallo: {e}")
            comparison[name] = {"error": str(e)}

    output_path = Path("resultados_comparacion.json")
    output_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nComparacion guardada en {output_path}")


if __name__ == "__main__":
    main()
