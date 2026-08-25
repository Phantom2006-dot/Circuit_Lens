# Circuit Lens v1.7 — Smart Perception Update

## What changed

Circuit Lens now uses a **two-level evidence model**. The component path marks visual candidates in the camera frame; the board path classifies the full board form factor; and the conclusion path ranks a board identity only when the board model reaches its confidence and separation gates. The interface no longer limits the record to four fixed object types. The **Objects marked in frame** panel now keeps all model candidates and lets the user search or filter by passive parts, semiconductors, power, connectors, modules, sensors, switches and motion devices, displays, and other classes.

| Stage | Real-data source | Current coverage | Output policy |
| --- | --- | --- | --- |
| Component detector | ElectroCom61 v2, CC BY 4.0 | 61 visual component/module labels | Candidate boxes only; all broad-model outputs are marked **Review**. [1] |
| Board classifier | IoTKITs v1, CC BY 4.0 | 15 board labels, including Arduino variants, ESP32-class boards, Jetson Nano/TX2, Raspberry Pi, STM32, and TelosB | Ranked board matches and a gated best-match conclusion. [2] |
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

ESP32-CAM and Jetson Orin Nano Super are documented in the board catalog but are currently **reference-only**. The IoTKITs training archive does not provide labelled photographs for those exact versions, and the only public ESP32-CAM dataset examined labels people in camera scenes rather than the physical module. Circuit Lens therefore does not claim learned recognition coverage for those exact boards yet. [2] [3]

## Recommended next steps

The next production model should replace the compact grid detector with a stronger modern detector trained on more varied board-level and component-level photographs, especially ESP32-CAM variants, ESP32-S3 camera boards, Jetson Orin kits, and board revisions in real benches. Each target board needs front/back images, scale/orientation variation, negative examples, silkscreen/connector close-ups, and an independent held-out test set. Electrical conclusions should additionally require schematic/BOM evidence and, where needed, meter or continuity measurements.

## References

[1] [Sayeedi et al., “ElectroCom61: A Multiclass Dataset for Detection of Electronic Components,” Mendeley Data, v2.](https://data.mendeley.com/datasets/6scy6h8sjz/2)

[2] [Đỗ Nguyễn, “IoTKITs,” Mendeley Data, v1.](https://data.mendeley.com/datasets/x5thzmkxhy/1)

[3] [Roboflow Universe, “esp32-cam Object Detection Dataset.”](https://universe.roboflow.com/pracainzynierska/esp32-cam)
