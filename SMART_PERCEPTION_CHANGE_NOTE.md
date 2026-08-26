# Circuit Lens v1.7.2 — Smart Perception and Module Recognition Update

## What changed

Circuit Lens now uses a **two-level evidence model**. The component path marks visual candidates in the camera frame; the board path classifies the full board form factor; and the conclusion path ranks a board identity only when the board model reaches its confidence and separation gates. The interface no longer limits the record to four fixed object types. The **Objects marked in frame** panel now keeps all model candidates and lets the user search or filter by passive parts, semiconductors, power, connectors, modules, sensors, switches and motion devices, displays, and other classes.

| Stage | Real-data source | Current coverage | Output policy |
| --- | --- | --- | --- |
| Component detector | ElectroCom61 v2, CC BY 4.0 | 61 visual component/module labels | Candidate boxes only; all broad-model outputs are marked **Review**. [1] |
| Board classifier | IoTKITs v1, CC BY 4.0 | 15 board labels, including Arduino variants, ESP32-class boards, Jetson Nano/TX2, Raspberry Pi, STM32, and TelosB | Ranked board matches and a gated best-match conclusion. [2] |
| Silkscreen evidence | Tesseract OCR plus a curated exact-marking allow-list | ESP32-CAM, ESP32-WROOM-32, ESP32-S3-DevKitC, ESP32 development boards, ESP8266/Wemos, selected Arduino boards including Nano ESP32, and Jetson Nano/TX2 | A clear, exact board/module marking can support a direct candidate conclusion; generic text is discarded. [4] [5] [6] |
| Topology analyzer | Image trace, terminal, and component evidence | Candidate links, nets, and familiar circuit-pattern hypotheses | Review-only; cannot see hidden layers, net names, or electrical continuity. |
| Catalog | Official manufacturer/product documentation | Board and component reference records | Context and verification links, not visual proof of an exact part. |

## Broader marked-object vocabulary

The full ElectroCom61 path includes resistors, multiple capacitor types, inductors, thermistors, diodes, Zener diodes, BJTs, MOSFETs, IGBTs, bridge rectifiers, ICs, motors, relays, switches, pin headers, batteries, buck converters, LEDs, displays, ESP32/ESP32-CAM labels, Bluetooth/GSM/RFID modules, sensor modules, and common Arduino board labels. Each candidate is assigned a taxonomy family so the interface can remain navigable when a frame contains many marked objects.

> The visual label is a **candidate class**, not a declaration of exact electrical value, package pinout, board revision, or safe circuit function. The UI preserves all candidates but makes review status visible rather than silently promoting uncertain labels.

## Measured model status

The bundled board model was trained from IoTKITs annotation crops and evaluated on its held-out validation crops. It achieved **81.87% top-1 accuracy** and **78.14% macro recall** across 651 validation images. Performance varies substantially by class, so its board conclusions are gated and include alternatives rather than being treated as facts.

The full 61-class component TinyGrid model was trained on the ElectroCom61 training split for 20 CPU epochs. At the selected 0.60 candidate threshold on the held-out test split, the compact baseline obtained **10.39% precision** and **13.32% recall** at IoU 0.50. This is not adequate for verified component identification. It is included to enable the broader object vocabulary and the interface workflow, but its detections are deliberately emitted as **review-only**. A production release needs a stronger detector, per-class calibration, mAP reporting, and task-specific photo collection.

## How a hardware conclusion is produced

The board classifier supplies the top ranked board identities. Circuit Lens compares the leading score with the next-best score and only labels the result a `candidate_conclusion` if the leading supported class clears **70% confidence** and a **12-point margin**. Component/module detections are recorded as supporting evidence, while connectors, board outline, camera, RF, and header geometry remain listed as expected visual evidence. If the gate fails, the interface says **No reliable board conclusion from this frame** and asks for a wider, sharper capture rather than forcing a guess.

ESP32-CAM and Jetson Orin Nano Super are documented in the board catalog but are currently **reference-only** as visual image-model classes. The IoTKITs training archive does not provide labelled photographs for those exact versions, and the only public ESP32-CAM dataset examined labels people in camera scenes rather than the physical module. Circuit Lens therefore does not claim learned recognition coverage for those exact boards yet. [2] [3]

## Direct silkscreen evidence for Arduino and ESP modules

Circuit Lens now adds a separate OCR pass when the user selects **Identify circuit board**. It enlarges, converts, sharpens, and contrast-enhances the frame before running Tesseract locally in the backend. The output is not treated as open-ended OCR. Instead, only a short allow-list of high-specificity exact phrases is retained. This includes `ESP32-CAM`, `AI-THINKER`, `ESP-WROOM-32`, `ESP32-S3-DEVKITC`, `ARDUINO UNO`, `ARDUINO NANO ESP32`, `MEGA 2560`, `WEMOS`, and selected Jetson identifiers.

| Evidence observed | Circuit Lens behavior | Reliability boundary |
| --- | --- | --- |
| `ESP32-CAM` or `AI-THINKER` is read clearly | Produces an **ESP32-CAM** candidate conclusion and shows the exact marking in the conclusion card. | This is a direct marking-based identification, not a claim that ESP32-CAM photographs trained the board classifier. |
| `ARDUINO NANO ESP32` is read clearly | Produces an **Arduino Nano ESP32** candidate conclusion, ahead of the broader `ESP32` phrase also present in the name. | Specificity is resolved by preferring the longest exact marking, so generic ESP32 text cannot override the full Arduino board name. |
| Only generic `ESP`, `Arduino`, logos, or ambiguous shapes are visible | Produces no OCR evidence; the board classifier and its confidence/margin gate remain in charge. | The interface returns **needs more evidence** rather than guessing an exact module. |
| A trained IoTKITs board class has a strong, separated score | Produces the usual classifier-backed candidate conclusion with alternatives. | The conclusion remains a camera-based candidate; board revision, electrical condition, and pin function still require verification. |

> A silkscreen conclusion requires a sharp, front-facing capture with the relevant text visible. OCR cannot establish a board revision, a counterfeit/clone relationship, pin mapping, wiring correctness, or safe electrical state. It is therefore shown with the exact phrase read and an engineering-review next-capture instruction.

The catalog now includes marking-assisted references for the Espressif ESP32-WROOM-32 module and ESP32-S3-DevKitC-1, as well as Arduino Nano ESP32. Those records provide visual cues, technical context, and manufacturer documentation, but their `supported_by_trained_model` field remains false until dedicated, labelled image data is trained and independently evaluated. Espressif documents the WROOM-32 as a Wi-Fi/Bluetooth module and the S3-DevKitC-1 as an ESP32-S3 development board; Arduino documents Nano ESP32 as using the NORA-W106 module with an ESP32-S3 chip. [4] [5] [6]

For deployment, the backend image installs `tesseract-ocr` and the production environment continues to supply both TorchScript model paths plus `ALLOWED_ORIGINS`. The frontend hardware-conclusion card displays **“Marking read”** whenever the backend returns curated evidence. This makes the evidence path inspectable rather than presenting an unqualified board name.

## Recommended next steps

The next production model should replace the compact grid detector with a stronger modern detector trained on more varied board-level and component-level photographs, especially ESP32-CAM variants, ESP32-S3 camera boards, Jetson Orin kits, and board revisions in real benches. Each target board needs front/back images, scale/orientation variation, negative examples, silkscreen/connector close-ups, and an independent held-out test set. Electrical conclusions should additionally require schematic/BOM evidence and, where needed, meter or continuity measurements.

## References

[1] [Sayeedi et al., “ElectroCom61: A Multiclass Dataset for Detection of Electronic Components,” Mendeley Data, v2.](https://data.mendeley.com/datasets/6scy6h8sjz/2)

[2] [Đỗ Nguyễn, “IoTKITs,” Mendeley Data, v1.](https://data.mendeley.com/datasets/x5thzmkxhy/1)

[3] [Roboflow Universe, “esp32-cam Object Detection Dataset.”](https://universe.roboflow.com/pracainzynierska/esp32-cam)

[4] [Espressif, “ESP32-WROOM-32 Datasheet.”](https://documentation.espressif.com/esp32-wroom-32_datasheet_en.html)

[5] [Espressif, “ESP32-S3-DevKitC-1.”](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/index.html)

[6] [Arduino, “Nano ESP32.”](https://docs.arduino.cc/hardware/nano-esp32)
