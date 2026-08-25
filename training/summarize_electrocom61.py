"""Create a reproducible manifest from the downloaded ElectroCom61 v2 dataset.

Usage: python summarize_electrocom61.py --dataset data/electrocom61 --output data/electrocom61_stats.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from electrocom61 import CANONICAL_FAMILIES, dataset_names, image_label_pairs, target_class_map


parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

mapping = target_class_map(args.dataset)
split_images: dict[str, int] = {}
split_labels: dict[str, dict[str, int]] = {}
for split in ("train", "valid", "test"):
    counter: Counter[str] = Counter()
    image_count = 0
    for _, labels in image_label_pairs(args.dataset, split, mapping):
        image_count += 1
        for family_index, *_ in labels:
            counter[CANONICAL_FAMILIES[family_index]] += 1
    split_images[split] = image_count
    split_labels[split] = {family: counter[family] for family in CANONICAL_FAMILIES}

payload = {
    "dataset": "ElectroCom61 v2",
    "doi": "10.17632/6scy6h8sjz.2",
    "license": "CC BY 4.0",
    "source_url": "https://data.mendeley.com/datasets/6scy6h8sjz/2",
    "original_class_count": len(dataset_names(args.dataset)),
    "canonical_families": CANONICAL_FAMILIES,
    "mapped_original_classes": {str(index): dataset_names(args.dataset)[index] for index in sorted(mapping)},
    "images_with_target_labels": split_images,
    "annotations_by_split": split_labels,
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
