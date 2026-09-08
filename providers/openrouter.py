"""Extraccion de LOTE y fecha de vencimiento usando OpenRouter.

Solo se llama desde main.py con run(prompt). Necesita OPENROUTER_API_KEY en
el entorno (.env). Modelo configurable con OPENROUTER_MODEL (default:
google/gemini-3.6-flash).

Requiere el paquete "openai" (pip install openai): OpenRouter expone un
endpoint compatible con la API de OpenAI.
"""
from __future__ import annotations

import base64
import json
import os

import certifi
import httpx2
from openai import OpenAI

from common import EXTRACTION_SCHEMA, error_entry, get_photo_paths, media_type_for, save_results

PROVIDER_NAME = "openrouter"
MODEL = os.getenv("OPENROUTER_MODEL")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# OpenRouter no garantiza json_schema estricto para todos los modelos
# subyacentes, asi que forzamos JSON via response_format json_object y le
# pasamos el schema comun (common.py) como instruccion en el system prompt.
_SYSTEM_PROMPT = (
    "Respondes UNICAMENTE con un objeto JSON que cumpla exactamente este "
    "JSON Schema, sin texto adicional ni bloques de codigo:\n"
    + json.dumps(EXTRACTION_SCHEMA, ensure_ascii=False)
)


def _extract_one(client: OpenAI, prompt: str, image_path) -> dict:
    image_b64 = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    data_url = f"data:{media_type_for(image_path)};base64,{image_b64}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content)
    data["imagen"] = image_path.name
    return data


def run(prompt: str) -> list[dict]:
    """Procesa todas las fotos de photos/ y devuelve/guarda los resultados."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Falta OPENROUTER_API_KEY en el entorno (.env)")

    # verify=certifi.where() evita que httpx2 use truststore, cuyo backend de
    # Windows tiene un bug de recursion infinita en Python 3.14 (ver README/nota).
    http_client = httpx2.Client(verify=certifi.where())
    client = OpenAI(api_key=api_key, base_url=BASE_URL, http_client=http_client)
    results = []
    for photo in get_photo_paths():
        try:
            results.append(_extract_one(client, prompt, photo))
        except Exception as e:
            results.append(error_entry(photo.name, e))
        print(f"[{PROVIDER_NAME}] {photo.name} procesada")

    save_results(PROVIDER_NAME, results)
    print(f"[{PROVIDER_NAME}] modelo usado: {MODEL}")
    return results
