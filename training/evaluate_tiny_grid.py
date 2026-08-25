"""Evaluate the TinyGrid TorchScript baseline on ElectroCom61 test labels.

This computes class-aware, IoU=0.50 single-threshold precision and recall. It is
not a replacement for full COCO mAP reporting, but it provides an honest local
quality gate before the model is exposed as a live inspection candidate source.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

from electrocom61 import CANONICAL_FAMILIES, image_label_pairs, target_class_map

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))
from app.contracts import BoundingBox  # noqa: E402
from app.detector import TinyGridTorchScriptDetector, _iou  # noqa: E402


parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=Path, required=True)
parser.add_argument("--model", type=Path, required=True)
parser.add_argument("--threshold", type=float, default=0.20)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

detector = TinyGridTorchScriptDetector(args.model, args.threshold)
mapping = target_class_map(args.dataset)
tp = fp = fn = 0
per_family = {family: {"tp": 0, "fp": 0, "fn": 0} for family in CANONICAL_FAMILIES}
for image_path, labels in image_label_pairs(args.dataset, "test", mapping):
    actual = [(CANONICAL_FAMILIES[family_index], BoundingBox(x=(cx - width / 2) * 100, y=(cy - height / 2) * 100, width=width * 100, height=height * 100)) for family_index, cx, cy, width, height in labels]
    unmatched = set(range(len(actual)))
    predictions = detector.detect(Image.open(image_path))
    for prediction in predictions:
        matching = [index for index in unmatched if actual[index][0] == prediction.kind and _iou(actual[index][1], prediction.box) >= 0.50]
        if matching:
            best = max(matching, key=lambda index: _iou(actual[index][1], prediction.box))
            unmatched.remove(best)
            tp += 1
            per_family[prediction.kind]["tp"] += 1
        else:
            fp += 1
            per_family[prediction.kind]["fp"] += 1
    for index in unmatched:
        family = actual[index][0]
        fn += 1
        per_family[family]["fn"] += 1

def metrics(values: dict[str, int]) -> dict[str, float | int]:
    precision = values["tp"] / (values["tp"] + values["fp"]) if values["tp"] + values["fp"] else 0.0
    recall = values["tp"] / (values["tp"] + values["fn"]) if values["tp"] + values["fn"] else 0.0
    return {**values, "precision": round(precision, 4), "recall": round(recall, 4)}

payload = {
    "dataset": "ElectroCom61 v2 test split",
    "metric": "Class-aware single-threshold precision/recall at IoU ≥ 0.50",
    "threshold": args.threshold,
    "overall": metrics({"tp": tp, "fp": fp, "fn": fn}),
    "by_family": {family: metrics(values) for family, values in per_family.items()},
    "caveat": "TinyGrid is a compact baseline. Use these measurements for regression tracking, not as a production-performance claim.",
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
