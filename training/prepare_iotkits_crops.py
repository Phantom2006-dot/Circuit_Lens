"""Create real board crops from IoTKITs COCO annotations for classification."""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from PIL import Image

from iotkits import canonical_board, load_coco


parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
counts = Counter()
for split in ("train", "valid"):
    coco = load_coco(args.dataset, split)
    categories = {category["id"]: category["name"] for category in coco["categories"]}
    images = {item["id"]: item for item in coco["images"]}
    for index, annotation in enumerate(coco["annotations"]):
        board = canonical_board(categories[annotation["category_id"]])
        if not board:
            continue
        source = args.dataset / split / images[annotation["image_id"]]["file_name"]
        if not source.is_file():
            continue
        x, y, width, height = annotation["bbox"]
        with Image.open(source) as image:
            padding = int(max(width, height) * .08)
            crop = image.crop((max(0, int(x) - padding), max(0, int(y) - padding), min(image.width, int(x + width) + padding), min(image.height, int(y + height) + padding))).convert("RGB")
            destination = args.output / split / board
            destination.mkdir(parents=True, exist_ok=True)
            crop.save(destination / f"{source.stem}_{index}.jpg", quality=92)
            counts[f"{split}/{board}"] += 1
print("\n".join(f"{key}: {value}" for key, value in sorted(counts.items())))
