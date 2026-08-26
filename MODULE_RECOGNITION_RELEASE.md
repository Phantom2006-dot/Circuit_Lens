# Circuit Lens v1.7.2 — Module Recognition Release

Circuit Lens v1.7.2 strengthens the **Identify circuit board** mode without weakening its evidence safeguards. The release combines the existing IoTKITs board classifier with a bounded OCR path for legible module silkscreen. This gives a camera frame two legitimate ways to produce a usable candidate conclusion: a strong trained board-classifier result or a clear, exact module/board marking.

| Capability | What is now supported | What is not claimed |
| --- | --- | --- |
| Trained board classification | The bundled IoTKITs TorchScript classifier ranks 15 board-level classes, including Arduino variants, an ESP32 development-board class, ESP8266/Wemos, Jetson Nano/TX2, Raspberry Pi, STM32, and TelosB. [1] | A classifier score does not prove board revision, connector pinout, electrical health, or circuit function. |
| Exact marking evidence | Curated OCR signatures can identify ESP32-CAM/AI-Thinker, ESP32-WROOM-32, ESP32-S3-DevKitC, ESP8266/Wemos, selected Arduino boards including Arduino Nano ESP32, and selected Jetson modules when the text is visible. [2] [3] [4] | Generic words, logos, and ambiguous OCR strings never trigger a direct conclusion. |
| Component analysis | The ElectroCom61 model can return 61 component/module candidate labels for review. [5] | Current measured component-detection quality does not support verified part, value, pinout, or safety claims. |

The exact marking is deliberately surfaced in the hardware conclusion card as **“Marking read: …”**. If text is absent or too blurred, Circuit Lens does not substitute a generic ESP/Arduino guess. Instead it retains the classifier ranking and, when the confidence/margin gate is not met, returns **No reliable board conclusion from this frame** with a request for a wider, sharper capture.

> The preferred capture for module identification is a non-reflected rear-camera image of the complete front side. Keep the USB connector, RF can/antenna area, headers, camera socket where applicable, and silkscreen in focus. Capture the reverse side separately when revision markings are there.

The feature is wired into the separately deployable backend image. Its Dockerfile installs Tesseract, while `env.template` specifies component-model paths, board-model paths, the 0.60 component candidate threshold, and allowed frontend origins. The Vercel-oriented frontend keeps its API URL in `VITE_API_BASE_URL`; the hosted preview uses its temporary public API endpoint.

## Verified release checks

| Check | Result |
| --- | --- |
| ESP32-CAM/AI-Thinker marking smoke test | Passed: a synthetic high-contrast marking produced an ESP32-CAM candidate conclusion. |
| Arduino Nano ESP32 marking smoke test | Passed: the full Arduino marking outranked incidental generic ESP32 text and produced an Arduino Nano ESP32 candidate conclusion. |
| Backend API, topology, hardware, and TorchScript smoke suites | Passed. The preserved real component fixture returned **needs more evidence** for board identity, as expected. |
| Hosted preview build and deployable frontend build | Passed. |
| Preview CORS and model health | Passed: the temporary endpoint reported both component and board models in `torchscript` mode and permitted the hosted preview origin. |

## References

[1] [Đỗ Nguyễn, “IoTKITs,” Mendeley Data, v1.](https://data.mendeley.com/datasets/x5thzmkxhy/1)

[2] [Espressif, “ESP32-WROOM-32 Datasheet.”](https://documentation.espressif.com/esp32-wroom-32_datasheet_en.html)

[3] [Espressif, “ESP32-S3-DevKitC-1.”](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/index.html)

[4] [Arduino, “Nano ESP32.”](https://docs.arduino.cc/hardware/nano-esp32)

[5] [Sayeedi et al., “ElectroCom61: A Multiclass Dataset for Detection of Electronic Components,” Mendeley Data, v2.](https://data.mendeley.com/datasets/6scy6h8sjz/2)
