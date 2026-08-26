"""Extract high-specificity module markings from a board photograph.

OCR is evidence, not a replacement for the trained board classifier. Exact
silkscreen markings can nevertheless be decisive for boards such as ESP32-CAM
when an image classifier has no labelled coverage for that exact revision.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


MARKING_SIGNATURES: dict[str, tuple[str, ...]] = {
    "esp32_cam": ("ESP32-CAM", "ESP32CAM", "AI-THINKER", "AI THINKER"),
    "esp32_wroom_32": ("ESP-WROOM-32", "ESP32-WROOM-32", "ESP32-WROOM"),
    "esp32_s3_devkitc": ("ESP32-S3-DEVKITC", "ESP32-S3", "ESP32S3"),
    "esp32_dev_board": ("ESP32", "ESP-WROOM", "ESP32-WROOM", "ESP32 DEVKIT", "DOIT ESP32"),
    "esp8266_wemos": ("ESP8266", "WEMOS", "D1 MINI", "NODEMCU"),
    "arduino_uno_r3": ("ARDUINO UNO", "UNO R3"),
    "arduino_nano": ("ARDUINO NANO", "NANO EVERY"),
    "arduino_nano_esp32": ("ARDUINO NANO ESP32", "NANO ESP32"),
    "arduino_mega_2560": ("ARDUINO MEGA", "MEGA 2560"),
    "arduino_leonardo": ("ARDUINO LEONARDO", "LEONARDO"),
    "arduino_micro": ("ARDUINO MICRO",),
    "arduino_pro_mini": ("PRO MINI",),
    "arduino_zero": ("ARDUINO ZERO",),
    "jetson_nano": ("JETSON NANO",),
    "jetson_tx2": ("JETSON TX2",),
}


def _prepare_for_ocr(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    long_edge = max(rgb.size)
    if long_edge < 1500:
        ratio = 1500 / long_edge
        rgb = rgb.resize((round(rgb.width * ratio), round(rgb.height * ratio)))
    grayscale = ImageOps.grayscale(rgb)
    return ImageEnhance.Contrast(grayscale).enhance(1.9).filter(ImageFilter.SHARPEN)


def extract_module_markings(image: Image.Image) -> list[str]:
    """Return only high-specificity board/module markings read from the frame.

    The OCR process is intentionally bounded and failure-safe. Generic words
    such as "ESP" or "Arduino" alone are not returned; they are too easy to
    hallucinate from traces and logos. Returned phrases must match a curated,
    board-specific signature.
    """
    prepared = _prepare_for_ocr(image)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as source:
        source_path = Path(source.name)
    try:
        prepared.save(source_path)
        result = subprocess.run(
            ["tesseract", str(source_path), "stdout", "--psm", "11", "-l", "eng"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []
        normalized = re.sub(r"\s+", " ", result.stdout.upper()).strip()
        found: list[str] = []
        for signatures in MARKING_SIGNATURES.values():
            for signature in signatures:
                if signature in normalized and signature not in found:
                    found.append(signature)
        return found
    except (OSError, subprocess.SubprocessError):
        return []
    finally:
        source_path.unlink(missing_ok=True)


def markings_for_board(board_id: str, markings: list[str]) -> list[str]:
    signatures = MARKING_SIGNATURES.get(board_id, ())
    return [marking for marking in markings if marking in signatures]


def board_from_direct_marking(markings: list[str]) -> str | None:
    """Return the most specific board supported directly by a silkscreen phrase."""
    matches = [
        (len(marking), board_id)
        for board_id, signatures in MARKING_SIGNATURES.items()
        for marking in markings
        if marking in signatures
    ]
    return max(matches, default=(0, None))[1]
