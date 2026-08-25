"""Summarize IoTKITs labels into Circuit Lens canonical board identities."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from iotkits import CANONICAL_BOARDS, canonical_board, load_coco


parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

report = {"dataset": "IoTKITs v1", "doi": "10.17632/x5thzmkxhy.1", "license": "CC BY 4.0", "canonical_boards": CANONICAL_BOARDS, "splits": {}, "unmapped_source_labels": []}
unmapped = set()
for split in ("train", "valid"):
    coco = load_coco(args.dataset, split)
    categories = {category["id"]: category["name"] for category in coco["categories"]}
    annotations = Counter()
    images = {annotation["image_id"]: canonical_board(categories[annotation["category_id"]]) for annotation in coco["annotations"]}
    for annotation in coco["annotations"]:
        mapped = canonical_board(categories[annotation["category_id"]])
        if mapped:
            annotations[mapped] += 1
        else:
            unmapped.add(categories[annotation["category_id"]])
    report["splits"][split] = {"annotations": dict(annotations), "images": dict(Counter(value for value in images.values() if value))}
report["unmapped_source_labels"] = sorted(unmapped)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2))
print(json.dumps(report["splits"], indent=2))
