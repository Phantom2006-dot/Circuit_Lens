"""Structured development-board catalog and evidence-fusion policy.

Board records are sourced product references. A record is not returned as an
identified board unless a classifier prediction exists and passes the configured
confidence and separation gates.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class BoardReference:
    id: str
    name: str
    manufacturer: str
    family: str
    supported_by_trained_model: bool
    model_evidence: tuple[str, ...]
    visual_cues: tuple[str, ...]
    source_title: str
    source_url: str
    specifications: dict[str, str]


BOARD_CATALOG: tuple[BoardReference, ...] = (
    BoardReference("arduino_uno_r3", "Arduino Uno R3", "Arduino", "Microcontroller board", True, ("ATmega328P", "USB Type-B", "barrel jack", "14 digital pins", "DIP or SMD MCU"), ("Blue rectangular board", "large USB Type-B connector", "black barrel jack", "two long header rows"), "Arduino UNO R3 hardware documentation", "https://docs.arduino.cc/hardware/uno-rev3/", {"MCU": "ATmega328P", "Digital I/O": "14", "Analog inputs": "6", "Clock": "16 MHz"}),
    BoardReference("arduino_nano", "Arduino Nano", "Arduino", "Microcontroller board", True, ("ATmega328P", "Mini-B USB", "breadboard form factor"), ("Narrow breadboard board", "Mini-B USB", "two 15-pin header rows"), "Arduino Nano hardware documentation", "https://docs.arduino.cc/hardware/nano/", {"Dimensions": "45 × 18 mm", "Form factor": "Breadboard friendly", "MCU": "ATmega328P"}),
    BoardReference("arduino_nano_esp32", "Arduino Nano ESP32", "Arduino", "Wireless microcontroller board", False, ("NORA-W106", "ESP32-S3", "USB-C connector", "Arduino Nano ESP32 silkscreen"), ("Nano form factor", "USB-C connector", "dual header rows", "NORA-W106 module"), "Arduino Nano ESP32 documentation", "https://docs.arduino.cc/hardware/nano-esp32", {"Module": "u-blox NORA-W106", "Chip": "ESP32-S3", "Wireless": "Wi-Fi and Bluetooth 5", "Current model status": "Marking-assisted reference until labelled photographs are added to training"}),
    BoardReference("arduino_mega_2560", "Arduino Mega 2560 Rev3", "Arduino", "Microcontroller board", True, ("ATmega2560", "54 digital pins", "16 analog inputs", "4 UARTs"), ("Large Arduino outline", "extra-long pin headers", "USB Type-B connector"), "Arduino Mega 2560 Rev3 hardware documentation", "https://docs.arduino.cc/hardware/mega-2560/", {"MCU": "ATmega2560", "Digital I/O": "54", "Analog inputs": "16", "UARTs": "4"}),
    BoardReference("arduino_due", "Arduino Due", "Arduino", "Microcontroller board", True, ("Arduino Due label", "ARM SAM3X family"), ("Large Arduino-compatible outline", "two USB ports", "extended headers"), "Arduino hardware documentation", "https://docs.arduino.cc/hardware/", {"Platform": "Arduino Due", "Architecture": "ARM"}),
    BoardReference("arduino_leonardo", "Arduino Leonardo", "Arduino", "Microcontroller board", True, ("Arduino Leonardo label", "ATmega32U4 family"), ("Arduino-sized board", "micro USB connector", "standard header arrangement"), "Arduino hardware documentation", "https://docs.arduino.cc/hardware/", {"Platform": "Arduino Leonardo", "Architecture": "AVR"}),
    BoardReference("arduino_micro", "Arduino Micro", "Arduino", "Microcontroller board", True, ("Arduino Micro label", "ATmega32U4 family"), ("Slim microcontroller board", "micro USB", "dual headers"), "Arduino hardware documentation", "https://docs.arduino.cc/hardware/", {"Platform": "Arduino Micro", "Architecture": "AVR"}),
    BoardReference("arduino_pro_mini", "Arduino Pro Mini", "Arduino-compatible", "Microcontroller board", True, ("Pro Mini silkscreen", "ATmega328P family"), ("Small USB-less board", "six-pin programming header", "dual pin rows"), "Arduino hardware documentation", "https://docs.arduino.cc/hardware/", {"Platform": "Arduino Pro Mini", "Architecture": "AVR"}),
    BoardReference("arduino_zero", "Arduino Zero", "Arduino", "Microcontroller board", True, ("Arduino Zero label", "SAMD21 family"), ("Arduino-sized board", "native USB", "debug connector"), "Arduino hardware documentation", "https://docs.arduino.cc/hardware/", {"Platform": "Arduino Zero", "Architecture": "ARM Cortex-M0+"}),
    BoardReference("esp32_dev_board", "ESP32 Development Board", "Espressif / compatible", "Wireless microcontroller board", True, ("ESP32 module", "dual header rows", "USB-to-UART interface"), ("Small narrow board", "metal RF can", "antenna zone", "two pin rows"), "Espressif ESP32-DevKitC documentation", "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/hw-reference/esp32/get-started-devkitc.html", {"Platform": "ESP32", "I/O": "Most I/O broken out to side headers", "Wireless": "Wi‑Fi and Bluetooth family"}),
    BoardReference("esp32_cam", "ESP32-CAM", "AI-Thinker compatible", "Wireless camera microcontroller board", False, ("ESP32-S module", "camera ribbon connector", "OV2640 camera", "microSD slot"), ("Compact board", "camera socket or attached camera", "metal RF can", "microSD connector"), "Espressif camera application reference", "https://docs.espressif.com/projects/esp-faq/en/latest/application-solution/camera-application.html", {"Platform": "ESP32 camera-capable family", "Camera support": "ESP32 camera driver", "Current model status": "Reference-only until ESP32-CAM images are added to training"}),
    BoardReference("esp32_wroom_32", "ESP32-WROOM-32 Module", "Espressif", "Wireless microcontroller module", False, ("ESP-WROOM-32 silkscreen", "metal RF can", "PCB antenna"), ("Compact castellated module", "metal RF shield", "meander antenna zone"), "Espressif ESP32-WROOM-32 documentation", "https://documentation.espressif.com/esp32-wroom-32_datasheet_en.html", {"Platform": "ESP32", "Wireless": "Wi-Fi and Bluetooth", "Current model status": "Marking-assisted reference until module photographs are added to training"}),
    BoardReference("esp32_s3_devkitc", "ESP32-S3-DevKitC-1", "Espressif", "Wireless microcontroller board", False, ("ESP32-S3-WROOM module", "USB connector", "dual pin headers"), ("Narrow development board", "ESP32-S3 module", "USB connector", "dual header rows"), "Espressif ESP32-S3-DevKitC-1 documentation", "https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/index.html", {"Platform": "ESP32-S3", "Wireless": "Wi-Fi and Bluetooth LE", "Current model status": "Marking-assisted reference until labelled photographs are added to training"}),
    BoardReference("esp8266_wemos", "ESP8266 / Wemos Board", "ESP8266 compatible", "Wireless microcontroller board", True, ("ESP8266 module", "small USB connector", "narrow two-header board"), ("Narrow board", "small RF module or antenna", "micro USB connector"), "IoTKITs board dataset label", "https://data.mendeley.com/datasets/x5thzmkxhy/1", {"Platform": "ESP8266 / Wemos class", "Model data": "IoTKITs CC BY 4.0"}),
    BoardReference("jetson_nano", "NVIDIA Jetson Nano", "NVIDIA", "Edge AI developer kit", True, ("Jetson module", "40-pin header", "heatsink or carrier-board layout"), ("Large carrier board", "40-pin GPIO header", "camera connector", "Jetson module/heatsink"), "IoTKITs board dataset label", "https://data.mendeley.com/datasets/x5thzmkxhy/1", {"Platform": "Jetson Nano", "Model data": "IoTKITs CC BY 4.0"}),
    BoardReference("jetson_tx2", "NVIDIA Jetson TX2", "NVIDIA", "Edge AI developer kit", True, ("Jetson TX2 module", "carrier board", "40-pin header"), ("Large carrier board", "Jetson module", "camera/display connectors"), "IoTKITs board dataset label", "https://data.mendeley.com/datasets/x5thzmkxhy/1", {"Platform": "Jetson TX2", "Model data": "IoTKITs CC BY 4.0"}),
    BoardReference("jetson_orin_nano_super", "NVIDIA Jetson Orin Nano Super Developer Kit", "NVIDIA", "Edge AI developer kit", False, ("Jetson Orin Nano module", "carrier board", "40-pin header"), ("Compact Jetson carrier", "module/heatsink", "camera/display connectors"), "NVIDIA Jetson Orin Nano Super Developer Kit", "https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/", {"AI performance": "67 INT8 TOPS", "GPU": "1024 CUDA cores / 32 tensor cores", "Memory": "8 GB LPDDR5", "Power": "7–25 W", "Current model status": "Reference-only until image data is added to training"}),
    BoardReference("raspberry_pi", "Raspberry Pi", "Raspberry Pi", "Single-board computer", True, ("Raspberry Pi board", "40-pin GPIO", "USB/Ethernet connector group"), ("Credit-card board", "40-pin GPIO header", "USB connectors", "HDMI"), "IoTKITs board dataset label", "https://data.mendeley.com/datasets/x5thzmkxhy/1", {"Model data": "IoTKITs CC BY 4.0"}),
    BoardReference("stm32_dev_board", "STM32 Development Board", "STMicroelectronics / compatible", "Microcontroller board", True, ("STM32 MCU", "ST-LINK or USB connector", "dual headers"), ("Small controller board", "USB/debug connector", "dual pin headers"), "IoTKITs board dataset label", "https://data.mendeley.com/datasets/x5thzmkxhy/1", {"Platform": "STM32 class", "Model data": "IoTKITs CC BY 4.0"}),
    BoardReference("telosb", "TelosB", "Crossbow / compatible", "Wireless sensor node", True, ("TelosB label", "sensor-node form factor"), ("Slim sensor board", "antenna region", "dual headers"), "IoTKITs board dataset label", "https://data.mendeley.com/datasets/x5thzmkxhy/1", {"Platform": "TelosB", "Model data": "IoTKITs CC BY 4.0"}),
)


def board_by_id(board_id: str) -> BoardReference | None:
    return next((board for board in BOARD_CATALOG if board.id == board_id), None)


def all_boards() -> list[dict[str, object]]:
    return [asdict(board) for board in BOARD_CATALOG]
