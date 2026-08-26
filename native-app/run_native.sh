#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export TORCH_PREFIX="${TORCH_PREFIX:-/usr/local/lib/python3.12/dist-packages/torch}"
export CIRCUIT_LENS_DATA_DIR="${CIRCUIT_LENS_DATA_DIR:-$ROOT/backend-cpp/data}"
export MODEL_PATH="${MODEL_PATH:-$ROOT/backend/models/electrocom61-61class-tiny-grid.pt}"
export MODEL_LABELS_PATH="${MODEL_LABELS_PATH:-$ROOT/backend/models/electrocom61-61class-tiny-grid.labels.json}"
export BOARD_MODEL_PATH="${BOARD_MODEL_PATH:-$ROOT/backend/models/iotkits-board-classifier.pt}"
export BOARD_MODEL_LABELS_PATH="${BOARD_MODEL_LABELS_PATH:-$ROOT/backend/models/iotkits-board-classifier.labels.json}"
export CONFIDENCE_THRESHOLD="${CONFIDENCE_THRESHOLD:-0.60}"
exec "$ROOT/native-app/build/circuit_lens_desktop"
