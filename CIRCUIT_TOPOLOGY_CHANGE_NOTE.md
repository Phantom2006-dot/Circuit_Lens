# Circuit Lens v1.6.1 — Orientation and Circuit-Topology Upgrade

## What changed

The live video was horizontally mirrored with `scaleX(-1)`, which made the scene move opposite to the physical rear camera. That transform has been removed from both the hosted preview and the deployable frontend. The live feed now preserves the **physical left-right orientation** of the camera frame, matching a normal rear-camera application. Detection coordinates, terminal coordinates, and trace sampling all operate in that same non-mirrored coordinate system.

Circuit Lens has also moved beyond a fixed resistor/transistor/diode/capacitor interface. The package now includes a taxonomy for the full **61-class ElectroCom61 vocabulary**, grouping visual component labels across power, passive, semiconductor, interconnect, controller/module, sensor/module, electromechanical, and display/support categories. The current model artifact remains the measured four-label baseline; `training/train_electrocom61_61class.py` is the reproducible replacement path for a full 61-label TorchScript model trained on the complete licensed dataset.[1]

| Capability | Current implementation | Operational status |
| --- | --- | --- |
| Physical camera orientation | Rear-camera frame is no longer mirrored. | Implemented and frontend builds pass. |
| Broad label vocabulary | Full ElectroCom61 label taxonomy and group mapping. | Implemented in training and interpretation code. |
| Full 61-class model path | 61-class TinyGrid training script exports TorchScript plus a label sidecar. | Ready to train once the complete data set is supplied locally. |
| Trace evidence | Grayscale path sampling scores short terminal-to-terminal paths for trace-like contrast evidence. | Implemented as conservative visual evidence, not netlist truth. |
| Terminals and graph | Candidate terminal positions, review-only links, connected candidate nets, and candidate circuit-pattern rules. | Implemented and tested on an actual ElectroCom61 fixture. |
| Candidate circuit function | Pattern hints for switching/driver, power filtering/conversion, controller subsystem, or unclassified region. | Review-only hypothesis; not an electrical diagnosis. |

## Circuit-topology analysis flow

The new `POST /v1/topology/analyze` endpoint accepts the same JPEG, PNG, or WebP frame format as component inference. It first detects visible candidate components. It then assigns visual terminal locations from the detected package class, measures trace-like evidence along short candidate terminal pairs, keeps only conservative candidate links, groups those links into candidate nets, and emits a review-only circuit-pattern hypothesis.

```text
Camera frame
  → component/model candidates
  → package-specific terminal proposal
  → pixel-path trace evidence
  → candidate terminal-link graph
  → candidate nets
  → review-only circuit-pattern hypothesis
```

This decomposition follows the general structure used in connectivity-reconstruction research: component detection, port localization, and graph/link inference are distinct stages rather than one opaque claim of electrical correctness.[2] It also follows the more conservative conclusion of PCB-photo reconstruction work: normal optical images cannot reliably expose covered, hidden, or internal copper layers, so visual output should be treated as an editable hypothesis subject to human verification.[3]

The UI includes **Analyze topology**. With a live camera armed, it captures the current 640-pixel-long-edge JPEG frame, sends it to the endpoint, and shows the highest candidate pattern, candidate-link count, and candidate-net count in an orange **review required** card. The user must still inspect both PCB sides, markings, continuity, and the schematic context before treating a candidate net or circuit function as valid.

## ElectroCom61 implementation boundary

ElectroCom61 v2 has 2,121 annotated component images, 61 classes, and an explicit train/validation/test split under CC BY 4.0.[1] The package retains the original class order in `backend/app/taxonomy.py`, not just a collapsed four-family presentation. The 61-class training script consumes the native YOLO labels, trains a 61-output TinyGrid head, and writes both:

```text
models/electrocom61-61class.pt
models/electrocom61-61class.labels.json
```

To deploy such a model, set `MODEL_PATH` and `MODEL_LABELS_PATH` to these outputs. The API reads the sidecar rather than assuming a hard-coded label order. This prevents a class-index mismatch when the trained model is upgraded.

> The bundled four-class baseline has been measured and is not yet accurate enough for verified component identification. It is intentionally presented as a review-only candidate source. The 61-class path is code-complete but has **not** been claimed to be trained or validated until the full model is actually trained and evaluated on the held-out split.

## Validation completed

| Check | Result |
| --- | --- |
| Original preview TypeScript check and production build | Passed |
| Standalone Vercel frontend production build | Passed |
| Backend catalog, image validation, and TorchScript smoke tests | Passed |
| Topology endpoint against a real ElectroCom61 fixture | Passed: 18 baseline component candidates, 36 terminal hypotheses, and 24 review links in the local smoke test. |
| Exposed temporary topology service | Returned `model_mode: torchscript`; live fixture request returned component, terminal-link, and topology output. |
| Browser-to-API cross-origin health check | Passed. |
| Physical browser camera test in the sandbox | Not available: permission-failure UI passed; a real device must be used to validate physical movement and live-frame uploads. |

## How to test on a phone

Open the preview over HTTPS, choose **Arm camera**, approve the rear-camera permission, and move a visually distinct item across the physical view. It should now travel in the same direction on screen. After holding a board steady, choose **Analyze topology**. The displayed hypothesis is useful for an inspection workflow, but it must be corrected or verified with a TOP/BOTTOM capture pair, a multimeter continuity check, and an engineer’s review.

## References

[1] [Sayeedi et al., “ElectroCom61: A multiclass dataset for detection of electronic components,” *Data in Brief* (2025), and the CC BY 4.0 dataset record.](https://data.mendeley.com/datasets/6scy6h8sjz/2)

[2] [Hu, Zhan & Tong, “Parsing Netlists of Integrated Circuits from Images via Graph Attention Network,” *Sensors* (2024).](https://pmc.ncbi.nlm.nih.gov/articles/PMC10781286/)

[3] [Maliński & Okarma, “Vision-Based Reconstruction of Electrical Schematics from Printed Circuit Board Photographs,” *Electronics* (2026).](https://www.mdpi.com/2079-9292/15/14/3125)

[4] [PRISM reference PCB dataset for semi-automatic connectivity and schematic reconstruction, CC BY 4.0.](https://zenodo.org/records/21101131)
