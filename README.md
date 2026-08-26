# Circuit Lens — Native C++ Application

Circuit Lens now runs as a **native C++ desktop application**. The primary executable combines a Qt 6 live-camera workspace with C++ TorchScript inference, OpenCV preprocessing, Tesseract silkscreen evidence, and the same evidence gates that protect against unsupported board conclusions.

| Directory | Purpose | Primary runtime |
| --- | --- | --- |
| `native-app/` | Qt 6 desktop camera application with Component and Board inspection modes | `circuit_lens_desktop` |
| `backend-cpp/` | Native C++ TorchScript/OCR core and optional HTTP API | `circuit_lens_native` |
| `backend/models/` | Bundled TorchScript model artifacts and label sidecars | Shared by both C++ executables |
| `frontend/` | Earlier React web client retained as an optional reference build | Not required for native inspection |
| `backend/` | Earlier Python service plus reproducible training utilities | Training / migration reference only |

## Build and run the full native app

Install the Ubuntu dependencies, make a compatible LibTorch C++ distribution available, and build the desktop application. The `TORCH_PREFIX` variable should point to the root of that distribution; the development environment validates the app with CPU LibTorch 2.7.1.

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

The executable uses the default available camera and calls the C++ inference engine directly. It does **not** make Python inference calls. Select **Analyze components** for review-only component candidates, or **Identify circuit board** to combine the board classifier and exact curated silkscreen evidence.

## Optional native C++ HTTP API

The optional service preserves the existing API paths for external clients while replacing the FastAPI runtime with C++.

```bash
cd backend-cpp
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j1
./run_server.sh
```

It exposes health, catalog, board, multipart component inference, board hardware identification, and review-only topology endpoints. Use `backend-cpp/env.template` as the configuration reference.

## Inspection safeguards

Component detections remain **Review** candidates because the measured broad-vocabulary component baseline is not sufficient for verified part identification. Board mode accepts a candidate only when the trained-model confidence/margin gate passes or a clear allowed direct marking, such as `ESP32-CAM`, `AI-THINKER`, or `ARDUINO NANO ESP32`, is read. The application does not infer electrical continuity, hidden PCB layers, exact part numbers, or safe operating conditions from a camera frame.

For build details, C++ architecture, validation results, limitations, and citations, read [NATIVE_CPP_MIGRATION.md](NATIVE_CPP_MIGRATION.md). The prior implementation reports remain available in [TECHNICAL_IMPLEMENTATION.md](TECHNICAL_IMPLEMENTATION.md), [CIRCUIT_TOPOLOGY_CHANGE_NOTE.md](CIRCUIT_TOPOLOGY_CHANGE_NOTE.md), [SMART_PERCEPTION_CHANGE_NOTE.md](SMART_PERCEPTION_CHANGE_NOTE.md), and [MODULE_RECOGNITION_RELEASE.md](MODULE_RECOGNITION_RELEASE.md).
