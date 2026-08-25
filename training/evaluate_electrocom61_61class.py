"""Evaluate the full 61-class TinyGrid detector on the ElectroCom61 test split."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

from electrocom61 import dataset_names

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))
from app.contracts import BoundingBox
from app.detector import TinyGridTorchScriptDetector, _iou


parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=Path, required=True)
parser.add_argument("--model", type=Path, required=True)
parser.add_argument("--labels", type=Path, required=True)
parser.add_argument("--threshold", type=float, default=0.20)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

labels: list[str] = json.loads(args.labels.read_text())
detector = TinyGridTorchScriptDetector(args.model, args.threshold, labels)
tp = fp = fn = 0
for image_path in sorted((args.dataset / "test" / "images").glob("*")):
    label_path = args.dataset / "test" / "labels" / f"{image_path.stem}.txt"
    actual = []
    if label_path.is_file():
        for row in label_path.read_text().splitlines():
            values = row.split()
            if len(values) != 5:
                continue
            class_id, cx, cy, width, height = map(float, values)
            actual.append((labels[int(class_id)], BoundingBox(x=(cx - width / 2) * 100, y=(cy - height / 2) * 100, width=width * 100, height=height * 100)))
    unmatched = set(range(len(actual)))
    for predicted in detector.detect(Image.open(image_path)):
        matching = [index for index in unmatched if actual[index][0] == predicted.kind.replace(" ", "-") and _iou(actual[index][1], predicted.box) >= .5]
        if matching:
            unmatched.remove(max(matching, key=lambda index: _iou(actual[index][1], predicted.box)))
            tp += 1
        else:
            fp += 1
    fn += len(unmatched)
precision = tp / (tp + fp) if tp + fp else 0.0
recall = tp / (tp + fn) if tp + fn else 0.0
report = {"dataset": "ElectroCom61 v2 CC BY 4.0", "split": "test", "classes": len(labels), "threshold": args.threshold, "iou": 0.5, "true_positives": tp, "false_positives": fp, "false_negatives": fn, "precision": round(precision, 4), "recall": round(recall, 4), "caveat": "This compact baseline expands class coverage but must meet stricter validation and calibration targets before being used for verified identification."}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
