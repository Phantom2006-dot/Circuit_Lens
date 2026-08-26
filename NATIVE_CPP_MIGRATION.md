# Circuit Lens Native C++ Migration

## Migration result

Circuit Lens now includes a **complete native C++ runtime**. The primary desktop executable is in `native-app/`; it opens a Qt 6 inspection workspace, accesses the system camera, samples frames directly through `QVideoSink`, and runs component or board analysis in-process. The native HTTP service in `backend-cpp/` is also C++, so the same models can serve non-desktop clients without a Python web runtime.

| Layer | Native implementation | Runtime role |
| --- | --- | --- |
| Desktop inspection client | Qt 6 Widgets and Qt Multimedia | Live camera, **Analyze components** / **Identify circuit board** modes, pause control, evidence record, and confidence messaging. [1] |
| Component and board inference | LibTorch C++ API with the existing TorchScript `.pt` models | Loads the 61-class ElectroCom61 TinyGrid component model and 15-class IoTKITs board classifier on CPU. [2] [3] |
| Image preprocessing | OpenCV | Decodes JPEG/PNG/WebP uploads, normalizes BGR/RGB conversion, resizes frames, and supplies model tensors. |
| Direct marking evidence | Tesseract C++ API | Reads candidate silkscreen and retains only curated exact phrases such as `ESP32-CAM`, `AI-THINKER`, and `ARDUINO NANO ESP32`. [4] |
| Optional local HTTP API | C++ HTTP service | Preserves `/health`, catalog, board, inference, topology, and hardware-identification routes for non-native clients. |

> **Important boundary:** the original React frontend remains in `frontend/` as a reference and optional web build. The application that performs live inspection is now `native-app/circuit_lens_desktop`, written in C++. Python remains only in the reproducible training utilities and in the one-time catalog-data export helper; it is not required to run the native desktop application or C++ inference service.

## Native inspection workflow

The desktop client creates a `QCamera` and gives its output to a `QVideoWidget`. Qt documents that `QVideoSink` emits individual frames through `videoFrameChanged`, which is the mechanism used to sample a frame at 1.25 seconds in component mode and 3 seconds in board mode. Frames are converted to OpenCV matrices and passed to the C++ engine. [1]

The C++ engine loads TorchScript with LibTorch. PyTorch documents TorchScript’s C++ interface specifically as a mechanism for loading and executing serialized models that were defined in Python, including use in no-Python production inference contexts. [2]

| User mode | Native C++ decision path | Safeguard |
| --- | --- | --- |
| **Analyze components** | Runs the 61-class TinyGrid detector and displays candidate detections. | All broad-vocabulary detections are **Review** only; values, package pinouts, and electrical claims are not asserted. |
| **Identify circuit board** | Runs the IoTKITs board classifier, C++ Tesseract silkscreen extraction, and evidence fusion. | A model conclusion requires the existing 70% confidence and 12-point margin gate. Exact curated silkscreen can provide marking-assisted evidence; generic `ESP` or `Arduino` alone cannot. |
| **Topology output** | Produces terminal-oriented, review-only visual evidence. | It explicitly does not establish nets, hidden layers, continuity, or safe electrical state. |

## Build and run on Ubuntu 24.04

Install the development dependencies and make a LibTorch C++ distribution available through `TORCH_PREFIX`. In the development environment used for this release, `TORCH_PREFIX` points at the CPU LibTorch files bundled with the installed PyTorch distribution. For a standalone deployment, point the same variable at a matching LibTorch distribution. PyTorch notes that its C++ API is beta-stability, so lock the LibTorch version used for validated releases. [2]

```bash
sudo apt-get install build-essential cmake pkg-config \
  libopencv-dev libtesseract-dev tesseract-ocr \
  nlohmann-json3-dev libcpp-httplib-dev \
  qt6-base-dev qt6-multimedia-dev libqt6multimediawidgets6

export TORCH_PREFIX=/path/to/libtorch

cd native-app
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j1
./run_native.sh
```

The app will use the default available camera. Select **Identify circuit board** before framing a full board, then make the silkscreen, USB/RF/camera areas, and headers legible. Tesseract’s documented C++ API supports initializing an English recognizer, supplying pixel data, and obtaining UTF-8 text; Circuit Lens bounds that output to its exact marking allow-list rather than trusting arbitrary OCR text. [4]

## Run the optional C++ HTTP service

```bash
cd backend-cpp
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j1

export CIRCUIT_LENS_DATA_DIR="$PWD/data"
export MODEL_PATH="../backend/models/electrocom61-61class-tiny-grid.pt"
export MODEL_LABELS_PATH="../backend/models/electrocom61-61class-tiny-grid.labels.json"
export BOARD_MODEL_PATH="../backend/models/iotkits-board-classifier.pt"
export BOARD_MODEL_LABELS_PATH="../backend/models/iotkits-board-classifier.labels.json"
export CONFIDENCE_THRESHOLD=0.60
./build/circuit_lens_native
```

## Verified checks

| Check | Result |
| --- | --- |
| Native C++ inference service compilation | Passed with LibTorch, OpenCV, Tesseract, JSON, and C++ HTTP dependencies. |
| Native C++ direct marking evidence | Passed: an OpenCV-rendered `ARDUINO NANO ESP32` frame yielded an Arduino Nano ESP32 candidate conclusion. |
| C++ HTTP contract | Passed for health, catalog, board, multipart inference, hardware conclusion, review-only topology, and CORS. |
| Native desktop startup | Passed in Qt offscreen smoke mode for five seconds with both TorchScript models loaded. |
| Physical camera validation | Requires a machine with a camera; the sandbox has no attached camera device. |

## References

[1] [Qt, “QVideoSink Class.”](https://doc.qt.io/qt-6/qvideosink.html)

[2] [PyTorch, “PyTorch C++ API.”](https://docs.pytorch.org/cppdocs/)

[3] [Đỗ Nguyễn, “IoTKITs,” Mendeley Data, v1.](https://data.mendeley.com/datasets/x5thzmkxhy/1)

[4] [Tesseract OCR, “C++ API Examples.”](https://tesseract-ocr.github.io/tessdoc/Examples_C++.html)

[5] [Sayeedi et al., “ElectroCom61: A Multiclass Dataset for Detection of Electronic Components,” Mendeley Data, v2.](https://data.mendeley.com/datasets/6scy6h8sjz/2)
