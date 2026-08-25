"""Report held-out IoTKITs board-classification accuracy, coverage, and per-class recall."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from board_model import IMAGE_SIZE


parser = argparse.ArgumentParser()
parser.add_argument("--crops", type=Path, required=True)
parser.add_argument("--model", type=Path, required=True)
parser.add_argument("--labels", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
labels: list[str] = json.loads(args.labels.read_text())
model = torch.jit.load(str(args.model), map_location="cpu").eval()
correct, total, by_label = 0, 0, {label: Counter() for label in labels}
with torch.no_grad():
    for expected, label in enumerate(labels):
        for path in sorted((args.crops / "valid" / label).glob("*.jpg")):
            image = Image.open(path).convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE))
            tensor = torch.from_numpy(np.asarray(image).copy()).permute(2, 0, 1).float().div(255).unsqueeze(0)
            predicted = int(model(tensor).argmax(1).item())
            by_label[label]["total"] += 1
            by_label[label]["correct"] += int(predicted == expected)
            correct += int(predicted == expected)
            total += 1
per_class = {label: {"samples": counts["total"], "recall": round(counts["correct"] / max(1, counts["total"]), 4)} for label, counts in by_label.items()}
report = {"dataset": "IoTKITs v1 CC BY 4.0", "split": "valid", "samples": total, "top1_accuracy": round(correct / max(1, total), 4), "macro_recall": round(sum(item["recall"] for item in per_class.values()) / len(per_class), 4), "per_class": per_class}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
