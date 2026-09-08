"""Utilidades compartidas por los proveedores (providers/openrouter.py).

Nada aqui depende de un SDK de IA en particular: solo maneja fotos,
el esquema JSON comun de salida y el guardado de resultados.
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).parent
PHOTOS_DIR = ROOT_DIR / "photos"

# Esquema JSON comun que le pedimos a los 4 proveedores. Cada proveedor lo
# adapta a la forma que su API espera para "structured outputs" (Anthropic y
# OpenAI aceptan este JSON Schema casi tal cual; Gemini necesita su propio
# formato, ver providers/gemini.py).
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "lote": {"type": ["string", "null"]},
        "fecha_cruda": {"type": ["string", "null"]},
        "venc_dia": {"type": ["integer", "null"]},
        "venc_mes": {"type": ["integer", "null"]},
        "venc_anio": {"type": ["integer", "null"]},
        "venc_precision": {"type": "string", "enum": ["dia", "mes", "nulo"]},
        "confianza": {"type": "string", "enum": ["alta", "media", "baja"]},
        "notas": {"type": ["string", "null"]},
    },
    "required": [
        "lote",
        "fecha_cruda",
        "venc_dia",
        "venc_mes",
        "venc_anio",
        "venc_precision",
        "confianza",
        "notas",
    ],
    "additionalProperties": False,
}

_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def get_photo_paths(photos_dir: Path = PHOTOS_DIR) -> list[Path]:
    """Devuelve las fotos ordenadas numericamente (1, 2, 3, ... 29)."""

    def leading_number(p: Path) -> int:
        match = re.match(r"(\d+)", p.stem)
        return int(match.group(1)) if match else 0

    paths = [p for p in photos_dir.iterdir() if p.is_file()]
    return sorted(paths, key=leading_number)


def encode_image_base64(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode("utf-8")


def media_type_for(path: Path) -> str:
    return _MEDIA_TYPES.get(path.suffix.lower(), "image/jpeg")


def save_results(provider: str, results: list[dict], output_dir: Path = ROOT_DIR) -> Path:
    output_path = output_dir / f"results_{provider}.json"
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def error_entry(image_name: str, error: Exception) -> dict:
    """Entrada de resultado cuando una imagen falla, para no tumbar todo el lote."""
    return {
        "imagen": image_name,
        "lote": None,
        "fecha_cruda": None,
        "venc_dia": None,
        "venc_mes": None,
        "venc_anio": None,
        "venc_precision": None,
        "confianza": None,
        "notas": None,
        "error": str(error),
    }
