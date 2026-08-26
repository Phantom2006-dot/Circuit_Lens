# Circuit Lens Inspection Reliability Release

## Why the inspection workflow changed

The earlier 61-class full-frame component detector was useful for broad visual exploration but was not sufficiently precise for a confident engineering conclusion. Its published ElectroCom61 evaluation at a 0.60 threshold measured **10.39% precision** and **13.32% recall** at IoU 0.5. A preserved resistor photograph also produced unrelated high-score full-frame candidates, confirming that the detector must remain review-only.

This release does not disguise that limitation by lowering the acceptance standard. Instead, it separates wide-view scanning from a still-image workflow that is better matched to the available training data.

| Workflow | Primary evidence | User-visible result | Boundary |
| --- | --- | --- |
| Live component scan | Full-frame 61-class TinyGrid detector | Review-only visual candidates | No component identity, value, or safe electrical claim is verified. |
| Snapshot/open-image component review | Centred close-up classifier trained from ElectroCom61 object crops | Ranked close-up candidates plus quality notes | The model achieved 61.42% top-1 on 2,600 held-out crops; all rankings remain review-only. |
| Board identification | IoTKITs board classifier, visual cues, and curated board markings | Candidate conclusion only when confidence/margin or exact board marking passes | Bare chips are not mislabeled as boards. |
| Bare microcontroller review | Curated exact package markings and package-family records | Separate marking-assisted microcontroller candidate | The complete marking and physical package still require confirmation. |

## Snapshot and correction workflow

The native C++ client now provides **Snapshot & Inspect** for a live camera frame and **Open Image & Inspect** for an existing JPEG, PNG, or WebP. The outcome records image dimensions, brightness, and focus proxy values before running the selected inspection path. For a component, the operator should centre one target. For a board, the full front side, connector layout, and silkscreen should be visible.

The **Tell us what it is** control appends a local JSONL correction record containing the timestamp, user-provided identity, active analysis mode, image reference, and displayed model outcome. It is deliberately not automatic retraining data. A correction should be curated and, where necessary, annotated with a bounding box before it can enter a future training release.

## Microcontroller coverage

The evidence catalog distinguishes controller packages from development boards. Exact marking signatures currently cover **ATmega328P**, **ATmega2560**, **ATmega32U4**, **STM32F103**, **STM32F401**, **RP2040**, **PIC16F877A**, **LPC1768**, **ESP32-D0WD**, and **ESP32-C3**. These are marking-assisted review candidates only. Generic words, package-shape guesses, and OCR fragments are not accepted as sufficient evidence.

| Test | Result |
| --- | --- |
| C++ direct-board marking smoke test | Passed with `ARDUINO NANO ESP32`. |
| C++ bare-microcontroller marking smoke test | Passed with `ATMEGA328P`, yielding a separate `atmega328p` review candidate. |
| C++ close-up model export/load | Passed with a 1.35 MB TorchScript artifact and label sidecar. |
| C++ HTTP contract | Passed for health, catalog, multipart component inference, and CORS. |
| Native Qt app startup | Passed in offscreen mode with detector, board classifier, close-up classifier, OCR, snapshot controls, correction controls, and microcontroller evidence enabled. |
| Physical camera test in this sandbox | Not available: no `/dev/video*` device is attached. |

## Practical capture guidance

Use diffuse light, avoid glare across IC markings, and make the text occupy a large part of the image. For a chip, capture the package face-on, with the complete top marking in focus. For a board, take a full-board picture first, then a second close-up of the controller and silkscreen. Use a correction only when you can independently verify the item from its package marking, schematic, BOM, or official reference.

## Sources

The component data and crop-training source is [ElectroCom61 v2](https://data.mendeley.com/datasets/6scy6h8sjz/2). Board-classifier data is [IoTKITs v1](https://data.mendeley.com/datasets/x5thzmkxhy/1). Manufacturer links for individual microcontrollers are embedded in the native `component_catalog.json` and shown in the desktop inspection record.
