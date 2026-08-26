"""Smoke test for Arduino and ESP module markings used in hardware conclusions."""
from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.hardware import fuse_hardware_evidence
from app.module_evidence import extract_module_markings


canvas = Image.new("RGB", (1600, 500), color="white")
draw = ImageDraw.Draw(canvas)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
draw.text((85, 160), "ESP32-CAM  AI-THINKER", fill="black", font=font)

markings = extract_module_markings(canvas)
assert "ESP32-CAM" in markings, markings
assert "AI-THINKER" in markings, markings

result = fuse_hardware_evidence([], [], "torchscript", markings)
assert result.conclusion == "ESP32-CAM", result
assert result.conclusion_status == "candidate_conclusion", result
assert "ESP32-CAM" in result.recognized_markings, result

nano_canvas = Image.new("RGB", (1800, 500), color="white")
nano_draw = ImageDraw.Draw(nano_canvas)
nano_draw.text((85, 160), "ARDUINO NANO ESP32", fill="black", font=font)
nano_markings = extract_module_markings(nano_canvas)
assert "ARDUINO NANO ESP32" in nano_markings, nano_markings
nano_result = fuse_hardware_evidence([], [], "torchscript", nano_markings)
assert nano_result.conclusion == "Arduino Nano ESP32", nano_result
print("Module evidence smoke test passed.")
