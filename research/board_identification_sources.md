# Board-Level Identification Sources

| Source | Verified scope | Circuit Lens use |
| --- | --- | --- |
| [IoTKITs v1, Mendeley Data](https://data.mendeley.com/datasets/x5thzmkxhy/1) | CC BY 4.0 COCO/segmentation data for embedded boards, including Arduino, ESP32, Raspberry Pi, and similar platforms. The downloadable archive contains 3,114 files across train/validation splits. | Real crops used to train and evaluate the bundled 15-class board classifier. |
| [Arduino Uno R3](https://docs.arduino.cc/hardware/uno-rev3/) | ATmega328P, 14 digital I/O, 6 analog inputs, 16 MHz, USB and power-jack form factor. | Structured conclusion evidence and board reference. |
| [Arduino Nano](https://docs.arduino.cc/hardware/nano/) | 45 × 18 mm breadboard-friendly board with Mini-B USB. | Structured conclusion evidence and board reference. |
| [Arduino Mega 2560](https://docs.arduino.cc/hardware/mega-2560/) | ATmega2560, 54 digital pins, 16 analog inputs, and 4 UARTs. | Structured conclusion evidence and board reference. |
| [Espressif ESP32-DevKitC](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/hw-reference/esp32/get-started-devkitc.html) | ESP32 development board with I/O broken out to both side headers. | Structured ESP32 board reference. |
| [NVIDIA Jetson Orin Nano Super Developer Kit](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/) | 67 INT8 TOPS, 8 GB LPDDR5, 1024 CUDA cores, and 7–25 W operating power. | Structured reference only; no current model-training images in IoTKITs. |
| [Roboflow ESP32-CAM listing](https://universe.roboflow.com/pracainzynierska/esp32-cam) | CC BY 4.0, 86 images; its single annotated class is `person`, so it labels subjects seen by an ESP32-CAM, not the physical board. | Explicitly **not** used for board classification. ESP32-CAM stays reference-only until appropriate annotated board photographs are added. |

## Component-recognition data

[ElectroCom61 v2](https://data.mendeley.com/datasets/6scy6h8sjz/2) is CC BY 4.0 and provides 2,121 annotated component images in 61 classes. Images were captured under varied lighting, backgrounds, and viewing angles, standardized to 640 × 640, and split into train (70%), validation (20%), and test (10%) subsets. Circuit Lens uses it for the full component-recognition training path; the current small model remains a measured four-label baseline until the 61-class model is trained and evaluated.
