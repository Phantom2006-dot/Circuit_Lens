# Circuit Lens v1.6 — Computer Vision and PyTorch Implementation Note

## Purpose and current operating boundary

Circuit Lens now contains a **runnable camera-to-inference path**, a compact PyTorch detector trained on a real electronic-component dataset, a curated technical reference catalog, and deployment configuration that separates the browser application from the inference service. It is designed as an inspection assistant: it turns a sampled live camera frame into **candidate component families**, then supplies manufacturer-linked reference information that a user can verify against markings, package geometry, a schematic, or a bill of materials.

> **Important operating boundary:** The bundled TinyGrid model is a real-data baseline, not a production-qualified identification engine. Its measured test performance is not sufficient for safety-critical, repair-authorizing, or design-verifying decisions. It is therefore deliberately labelled as a **review-only candidate source** in the API.

| Layer | Implementation | Responsibility |
| --- | --- | --- |
| Browser client | React + Vite | Requests camera access, samples a JPEG frame every 1.25 seconds, renders labels, and presents sourced reference records. |
| API service | FastAPI | Validates uploads, restricts cross-origin access, loads the TorchScript artifact, returns normalized component detections, and serves catalog records. |
| Baseline model | PyTorch TinyGrid, exported with TorchScript | Generates resistor, transistor, diode, and capacitor candidate boxes from a 256 × 256 RGB input. |
| Training data | ElectroCom61 v2 | Supplies real component photographs and YOLO annotations under CC BY 4.0. [1] [2] |
| Reference data | Manufacturer documentation | Grounds the catalog in part-specific electrical and mechanical records. [3] [4] [5] [6] [7] |

## Real data implementation: ElectroCom61

The project includes support for **ElectroCom61 v2**, a public CC BY 4.0 dataset of 2,121 annotated photographs across 61 electronic-component classes. Its documentation states that the images were captured across different lighting conditions, backgrounds, camera angles, and smartphone devices, and that the data is split into training, validation, and test partitions. [1] [2]

The source dataset contains more categories than the first Circuit Lens model needs. `training/electrocom61.py` keeps the original 61-class ID ordering, then maps the visual families relevant to the initial interface into four canonical classes. This includes BJT, MOSFET, and IGBT under **Transistor**; Zener and standard diode under **Diode**; and five capacitor variants under **Capacitor**. No synthetic shapes or simulated component labels are used in this path.

| Canonical Circuit Lens family | ElectroCom61 source classes mapped into it | Training annotations | Validation annotations | Test annotations |
| --- | --- | ---: | ---: | ---: |
| Resistor | `Resistor` | 118 | 33 | 18 |
| Transistor | `BJT-Transistor`, `MOSFET`, `IGBT` | 240 | 349 | 63 |
| Diode | `Diode`, `Zener-Diode` | 353 | 127 | 23 |
| Capacitor | `Capacitor-10mf`, `Capacitor-470mf`, `Film-Capacitor`, `High-Voltage-Ceramic-Capacitor`, `Low-Voltage-Ceramic-Capacitor`, `MLC-Capacitor` | 973 | 340 | 68 |

The source package is not bundled wholesale into the code ZIP. Instead, the package contains the reproducible data tools, an attribution manifest, the generated data statistics, and four small CC BY test fixtures for API testing. The scripts download or consume the full dataset locally when a user wants to retrain.

### Reproduce data preparation

From the `training/` directory, point the scripts at an extracted ElectroCom61 v2 download.

```bash
python summarize_electrocom61.py \
  --dataset data/electrocom61 \
  --output data/electrocom61_stats.json

python prepare_electrocom61_fixtures.py \
  --dataset data/electrocom61 \
  --output ../backend/tests/fixtures/electrocom61
```

The summarized manifest records the source DOI, licence, all mapped source classes, and the actual label counts above. This makes the initial data boundary inspectable rather than implicit.

## PyTorch model implementation

`backend/app/tiny_grid.py` defines `TinyGridDetector`, a compact convolutional detector. Four stride-two convolution blocks reduce a 256 × 256 image to a 16 × 16 prediction grid. Each cell predicts objectness, center offsets, width, height, and four family-class logits. `training/train_tiny_grid.py` converts the original YOLO labels into this grid target, balances sparse positive object cells with a weighted objectness loss, trains the model, and exports a portable TorchScript artifact.

The training run performed in this environment used every extracted training image that contains one of the four canonical families, a batch size of eight, and twelve epochs on CPU. The observed epoch loss fell from **1.7364** to **0.1850**. This demonstrates that the data loading, label normalization, forward pass, loss, optimizer, and TorchScript export are functioning. Training loss alone is not a usable estimate of field performance, so the project also contains `training/evaluate_tiny_grid.py`.

| Evaluation item | Observed value |
| --- | ---: |
| Held-out ElectroCom61 target-family annotations | 172 |
| Candidate threshold | 0.20 |
| IoU matching threshold | 0.50 |
| True positives | 32 |
| False positives | 563 |
| False negatives | 140 |
| Precision | 5.38% |
| Recall | 18.60% |

These measurements establish that this compact baseline is **operational but not production-ready**. It produces candidate boxes through the live API, but its false-positive rate is too high for a trustworthy engineering tool. The correct next technical step is to train a stronger detector such as a current YOLO-family or EfficientDet-family model on the complete 61-class dataset, retain the original train/validation/test separation, perform threshold calibration, and gate release on per-class mAP, precision, recall, and human review. ElectroCom61’s own study reports much higher results for different, stronger model experiments; those values are not claimed for the Circuit Lens baseline. [1]

## Live camera inspection flow

When the technician chooses **Arm camera**, the browser requests an environment-facing camera through `getUserMedia`. When the feed is available and `VITE_API_BASE_URL` is configured, the client performs the following sequence every 1.25 seconds.

1. It draws the current `<video>` frame to an invisible canvas whose long edge is limited to 640 pixels.
2. It encodes the canvas as JPEG at quality 0.82, reducing bandwidth before transfer.
3. It submits the frame as multipart form data to `POST /v1/detections/infer`.
4. The FastAPI service accepts only JPEG, PNG, and WebP; rejects payloads over 12 MB; decodes the image with Pillow; then calls the loaded TorchScript model.
5. The model scores grid cells and converts retained candidates to percentage-based bounding boxes. Class-aware non-maximum suppression removes overlapping candidates of the same family.
6. The browser receives the normalized `CircuitDetection[]` response, updates the overlay and selected component, and fetches a matching technical reference card from `GET /v1/catalog/{family}`.

The browser never contains model weights, and the package does not add camera frames to a database, file store, or analytics endpoint. A deployment should use HTTPS and should configure `ALLOWED_ORIGINS` to the exact Vercel application origin. This is a sampling workflow, not a 30-FPS streaming inference system. Sampling is intentional: it controls bandwidth, provides time for inference, and makes it feasible to switch the web camera adapter to a React Native camera adapter later.

## Technical reference catalog

The backend catalog is deliberately separate from vision. A visual classifier can suggest a component **family**, but it cannot safely identify an exact manufacturer part number from package shape alone. Circuit Lens therefore attaches a clearly labelled reference card, rather than claiming an exact match.

| Family | Reference record | Key sourced values |
| --- | --- | --- |
| Resistor | Vishay CRCW0603 1 kΩ reference | 1 kΩ, ±1%, ±100 ppm/K, 0603 case; the cited series covers 10 Ω to 1 MΩ. [3] |
| Transistor | onsemi 2N3904 | NPN, TO-92, VCEO 40 V, IC 200 mA continuous, 625 mW at 25 °C. [4] |
| Diode | onsemi 1N4148WS | SOD-323FL, VRRM 75 V, IF 150 mA continuous, VF 1 V maximum at 10 mA, 4 ns maximum recovery. [5] |
| Capacitor | KEMET C0603C104K5RACTU | 0.1 µF, ±10%, 50 VDC, X7R, 0603, −55 to +125 °C. [6] |
| Regulator | STMicroelectronics L7805CV | 5 V fixed output, up to 1.5 A, TO-220. [7] |
| Connector | Molex 0022232041 | 4 positions, 2.54 mm pitch, vertical through-hole male header. [8] |

The catalog gives engineers and learners useful numbers directly in the application, while retaining source links for design verification. Exact part selection still requires a bill of materials, package marking, schematic context, and applicable manufacturer data.

## What was done with the supplied archive

The supplied `Embedded_CV_Compression_Offline.zip` was inspected as reference material without executing its included code. It contains offline examples for synthetic shape classification, single-object detection, and segmentation. Those geometric-shape samples are not representative of physical circuit components, so they were **not used to train Circuit Lens**. The implementation instead uses the downloaded, annotated ElectroCom61 component images for the model path.

## Local verification performed

| Check | Result |
| --- | --- |
| Standalone React frontend type-check and production build | Passed |
| FastAPI health, catalog, demo, upload validation, and real-fixture smoke test | Passed |
| TorchScript model loading through FastAPI | Passed |
| Four real ElectroCom61 image fixtures submitted through `/v1/detections/infer` | Passed |
| ElectroCom61 label normalization and data-statistics generation | Passed |
| ElectroCom61 PyTorch baseline training and TorchScript export | Passed |
| Held-out real-data baseline evaluation | Completed; result documented above and below the production acceptance bar |

## Deployment notes

Deploy `frontend/` to Vercel and set `VITE_API_BASE_URL` to the deployed Fly.io API URL. Deploy `backend/` to Fly.io with the included Dockerfile and `fly.toml`; set `ALLOWED_ORIGINS` to the exact Vercel domain. The selected split keeps browser code and API/model code separate. Vercel’s Vite guidance requires browser-readable variables to use the `VITE_` prefix and includes an SPA rewrite pattern used by this package. [9]

The included Fly configuration starts with the real-data baseline at threshold 0.20 so the end-to-end inspection pipeline is demonstrable. Before any real-world use, replace the baseline file with a model that clears a documented acceptance threshold, then raise the confidence threshold based on validation data. The model artifact is included for reproducibility, but it must not be treated as an approved diagnostic or design-verification model.

## References

[1] [Sayeedi et al., “ElectroCom61: A multiclass dataset for detection of electronic components,” *Data in Brief* (2025).](https://pmc.ncbi.nlm.nih.gov/articles/PMC11847280/)

[2] [ElectroCom61 v2, Mendeley Data, CC BY 4.0.](https://data.mendeley.com/datasets/6scy6h8sjz/2)

[3] [Vishay, “D11/CRCW0603 e3 — Sample Kit Standard Thick Film Chip Resistors.”](https://www.vishay.com/doc/?20078)

[4] [onsemi, “2N3903, 2N3904 General Purpose Transistors.”](https://www.onsemi.com/pdf/datasheet/2n3903-d.pdf)

[5] [onsemi, “1N4148WS / 1N4448WS / 1N914BWS Small Signal Diodes.”](https://www.onsemi.com/pdf/datasheet/1n4148ws-d.pdf)

[6] [KEMET / YAGEO, “C0603C104K5RACTU component specification.”](https://search.kemet.com/component-documentation/download/specsheet/C0603C104K5RACTU)

[7] [STMicroelectronics, “L7805CV product page.”](https://estore.st.com/en/l7805cv-cpn.html)

[8] [Molex, “0022232041 product page.”](https://www.molex.com/en-us/products/part-detail/22232041)

[9] [Vercel, “Vite on Vercel.”](https://vercel.com/docs/frameworks/frontend/vite)
