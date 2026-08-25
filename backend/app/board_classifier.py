"""TorchScript adapter for the real IoTKITs development-board classifier."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass
class BoardPrediction:
    board_id: str
    confidence: float


@dataclass
class IoTKITsBoardClassifier:
    model_path: Path
    labels_path: Path
    def __post_init__(self) -> None:
        import numpy as np
        import torch
        self.np, self.torch = np, torch
        self.labels = json.loads(self.labels_path.read_text())
        self.model = torch.jit.load(str(self.model_path), map_location="cpu")
        self.model.eval()
    def classify(self, image: Image.Image, top_k: int = 3) -> list[BoardPrediction]:
        image = image.convert("RGB").resize((160, 160))
        tensor = self.torch.from_numpy(self.np.asarray(image).copy()).permute(2, 0, 1).float().div(255).unsqueeze(0)
        with self.torch.no_grad():
            scores = self.torch.softmax(self.model(tensor)[0], dim=0)
        values, indices = self.torch.topk(scores, k=min(top_k, len(self.labels)))
        return [BoardPrediction(board_id=self.labels[int(index)], confidence=round(float(value), 4)) for value, index in zip(values, indices)]


def create_board_classifier() -> IoTKITsBoardClassifier | None:
    model = Path(os.getenv("BOARD_MODEL_PATH", ""))
    labels = Path(os.getenv("BOARD_MODEL_LABELS_PATH", ""))
    return IoTKITsBoardClassifier(model, labels) if model.is_file() and labels.is_file() else None
