"""Copy one real CC BY ElectroCom61 test image per canonical family into backend fixtures.

Usage: python prepare_electrocom61_fixtures.py --dataset data/electrocom61 --output ../backend/tests/fixtures/electrocom61
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from electrocom61 import CANONICAL_FAMILIES, image_label_pairs, target_class_map


parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

mapping = target_class_map(args.dataset)
selected: dict[int, tuple[Path, list[tuple[int, float, float, float, float]]]] = {}
for image_path, labels in image_label_pairs(args.dataset, "test", mapping):
    for family_index, *_ in labels:
        selected.setdefault(family_index, (image_path, labels))
    if len(selected) == len(CANONICAL_FAMILIES):
        break

args.output.mkdir(parents=True, exist_ok=True)
manifest: list[dict[str, object]] = []
for family_index, family in enumerate(CANONICAL_FAMILIES):
    if family_index not in selected:
        continue
    image_path, labels = selected[family_index]
    destination = args.output / f"{family.lower()}-{image_path.name}"
    shutil.copy2(image_path, destination)
    manifest.append({"family": family, "file": destination.name, "source_split": "test", "all_canonical_yolo_labels": labels})

(args.output / "manifest.json").write_text(json.dumps({"dataset": "ElectroCom61 v2", "doi": "10.17632/6scy6h8sjz.2", "license": "CC BY 4.0", "fixtures": manifest}, indent=2), encoding="utf-8")
print(f"Prepared {len(manifest)} real-data fixture images.")
