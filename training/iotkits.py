"""IoTKITs COCO helpers for development-board recognition.

The public dataset contains fine-grained, sometimes color-specific labels. This
module maps them into stable board identities used by the Circuit Lens catalog.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


CANONICAL_BOARDS = {
    "arduino_uno_r3": "Arduino Uno R3",
    "arduino_nano": "Arduino Nano",
    "arduino_mega_2560": "Arduino Mega 2560",
    "arduino_due": "Arduino Due",
    "arduino_micro": "Arduino Micro",
    "arduino_pro_mini": "Arduino Pro Mini",
    "arduino_zero": "Arduino Zero",
    "arduino_leonardo": "Arduino Leonardo",
    "esp32_dev_board": "ESP32 Development Board",
    "esp32_cam": "ESP32-CAM",
    "esp8266_wemos": "ESP8266 / Wemos Board",
    "raspberry_pi": "Raspberry Pi",
    "jetson_nano": "NVIDIA Jetson Nano",
    "jetson_tx2": "NVIDIA Jetson TX2",
    "stm32_dev_board": "STM32 Development Board",
    "telosb": "TelosB",
}


def canonical_board(raw_label: str) -> str | None:
    label = re.sub(r"[^a-z0-9]+", " ", raw_label.lower())
    if "arduino" in label and "mega" in label:
        return "arduino_mega_2560"
    if "arduino" in label and "due" in label:
        return "arduino_due"
    if "arduino" in label and "micro" in label:
        return "arduino_micro"
    if "arduino" in label and "promini" in label:
        return "arduino_pro_mini"
    if "arduino" in label and "zero" in label:
        return "arduino_zero"
    if "arduino" in label and "leonardo" in label:
        return "arduino_leonardo"
    if "arduino" in label and "nano" in label:
        return "arduino_nano"
    if "arduino" in label and ("uno" in label or "unor" in label):
        return "arduino_uno_r3"
    if "esp32" in label and "cam" in label:
        return "esp32_cam"
    if "esp32" in label:
        return "esp32_dev_board"
    if "esp8266" in label or "wemos" in label or "d1 mini" in label:
        return "esp8266_wemos"
    if "raspberry" in label or "raspberrypi" in label:
        return "raspberry_pi"
    if "jetson" in label and "nano" in label:
        return "jetson_nano"
    if "jetson" in label and "tx2" in label:
        return "jetson_tx2"
    if "stm32" in label:
        return "stm32_dev_board"
    if "telos" in label:
        return "telosb"
    return None


def load_coco(dataset: Path, split: str) -> dict:
    return json.loads((dataset / split / "_annotations.coco.json").read_text())
