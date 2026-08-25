"""Label-aware TorchScript detection adapters for Circuit Lens."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .catalog import references_for_family
from .contracts import BoundingBox, CircuitDetection
from .taxonomy import ELECTROCOM61_LABELS, display_name, group_for_label
from .tiny_grid import GRID_SIZE, INPUT_SIZE


def _record(identifier: str, label: str, confidence: float, health: str, x: float, y: float, width: float, height: float, note: str) -> CircuitDetection:
    family = group_for_label(label)
    references = references_for_family(label)
    if not references:
        references = references_for_family("Resistor") if label == "Resistor" else []
    value = str(references[0]["reference_value"]) if references else f"{display_name(label)} visual candidate"
    return CircuitDetection(id=identifier, kind=display_name(label), family=family, ref=f"CAND-{identifier[-3:]}", confidence=round(confidence, 4), health=health, box=BoundingBox(x=max(0, x), y=max(0, y), width=min(width, 100), height=min(height, 100)), value=value, note=note)


def demo_detections() -> list[CircuitDetection]:
    samples = [("r7", "Resistor", 0.98, "Review", 16, 53, 17, 13), ("q2", "BJT-Transistor", 0.94, "Review", 47, 33, 20, 19), ("d1", "Diode", 0.89, "Review", 68, 57, 18, 12), ("c4", "MLC-Capacitor", 0.81, "Review", 42, 68, 13, 11)]
    return [_record(identifier, label, confidence, health, x, y, width, height, "Demonstration candidate only — confirm markings and topology before use.") for identifier, label, confidence, health, x, y, width, height in samples]


def _iou(a: BoundingBox, b: BoundingBox) -> float:
    left, top, right, bottom = max(a.x, b.x), max(a.y, b.y), min(a.x + a.width, b.x + b.width), min(a.y + a.height, b.y + b.height)
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    union = a.width * a.height + b.width * b.height - intersection
    return intersection / union if union else 0.0


def _nms(candidates: list[CircuitDetection], threshold: float = 0.35, maximum: int = 20) -> list[CircuitDetection]:
    retained: list[CircuitDetection] = []
    for candidate in sorted(candidates, key=lambda item: item.confidence, reverse=True):
        if len(retained) >= maximum:
            break
        if all(candidate.kind != existing.kind or _iou(candidate.box, existing.box) < threshold for existing in retained):
            retained.append(candidate)
    return retained


@dataclass
class TinyGridTorchScriptDetector:
    model_path: Path
    threshold: float
    labels: list[str]

    def __post_init__(self) -> None:
        import numpy as np
        import torch
        self.np, self.torch = np, torch
        self.model = torch.jit.load(str(self.model_path), map_location="cpu")
        self.model.eval()

    def detect(self, image: Image.Image) -> list[CircuitDetection]:
        image = image.convert("RGB").resize((INPUT_SIZE, INPUT_SIZE))
        tensor = self.torch.from_numpy(self.np.asarray(image).copy()).permute(2, 0, 1).float().div(255).unsqueeze(0)
        with self.torch.no_grad():
            output = self.model(tensor)[0]
        objectness, offsets, classes = self.torch.sigmoid(output[0]), self.torch.sigmoid(output[1:5]), self.torch.softmax(output[5:], dim=0)
        labels = self.labels if len(self.labels) == classes.shape[0] else ELECTROCOM61_LABELS[: classes.shape[0]]
        candidates: list[CircuitDetection] = []
        for row in range(GRID_SIZE):
            for column in range(GRID_SIZE):
                class_score, class_index = self.torch.max(classes[:, row, column], dim=0)
                confidence = float(objectness[row, column] * class_score)
                if confidence < self.threshold:
                    continue
                width, height = float(offsets[2, row, column]) * 36, float(offsets[3, row, column]) * 36
                x, y = (column + float(offsets[0, row, column])) / GRID_SIZE * 100 - width / 2, (row + float(offsets[1, row, column])) / GRID_SIZE * 100 - height / 2
                label = labels[int(class_index)]
                candidates.append(_record(f"{label.lower()}-{row}-{column}", label, confidence, "Likely" if confidence >= 0.75 else "Review", x, y, width, height, "Model candidate — validate package, markings, terminal assignment, and trace evidence before an engineering decision."))
        return _nms(candidates)


def create_detector() -> TinyGridTorchScriptDetector | None:
    model_path = Path(os.getenv("MODEL_PATH", ""))
    if not model_path.is_file():
        return None
    labels_path = Path(os.getenv("MODEL_LABELS_PATH", ""))
    labels = json.loads(labels_path.read_text()) if labels_path.is_file() else ["Resistor", "BJT-Transistor", "Diode", "MLC-Capacitor"]
    return TinyGridTorchScriptDetector(model_path=model_path, threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.55")), labels=labels)
