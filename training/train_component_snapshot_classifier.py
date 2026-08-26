"""Train a 61-class close-up component classifier from official ElectroCom61 bounding boxes.

This model is intentionally used only for saved/loaded close-up snapshots. The full-frame
detector remains review-only because wide circuit photos can contain multiple components.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageEnhance, ImageOps
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))
from app.tiny_grid import ELECTROCOM61_LABELS  # noqa: E402


IMAGE_SIZE = 160


class SnapshotClassifier(nn.Module):
    def __init__(self, classes: int) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, 2, 1), nn.BatchNorm2d(32), nn.SiLU(),
            nn.Conv2d(32, 64, 3, 2, 1), nn.BatchNorm2d(64), nn.SiLU(),
            nn.Conv2d(64, 128, 3, 2, 1), nn.BatchNorm2d(128), nn.SiLU(),
            nn.Conv2d(128, 192, 3, 2, 1), nn.BatchNorm2d(192), nn.SiLU(), nn.AdaptiveAvgPool2d(1),
        )
        self.classifier = nn.Sequential(nn.Dropout(.20), nn.Linear(192, classes))

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(image).flatten(1))


class ComponentCropDataset(Dataset):
    def __init__(self, root: Path, split: str, augment: bool) -> None:
        self.root, self.augment, self.items = root, augment, []
        for image_path in sorted((root / split / "images").glob("*")):
            label_path = root / split / "labels" / f"{image_path.stem}.txt"
            if not label_path.exists():
                continue
            for row in label_path.read_text().splitlines():
                values = row.split()
                if len(values) != 5:
                    continue
                class_id, cx, cy, width, height = map(float, values)
                self.items.append((image_path, int(class_id), cx, cy, width, height))

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int):
        image_path, class_id, cx, cy, width, height = self.items[index]
        image = Image.open(image_path).convert("RGB")
        full_w, full_h = image.size
        padding = random.uniform(.10, .22) if self.augment else .16
        left = max(0, int((cx - width / 2 - width * padding) * full_w))
        top = max(0, int((cy - height / 2 - height * padding) * full_h))
        right = min(full_w, int((cx + width / 2 + width * padding) * full_w))
        bottom = min(full_h, int((cy + height / 2 + height * padding) * full_h))
        image = image.crop((left, top, max(left + 1, right), max(top + 1, bottom)))
        if self.augment:
            if random.random() < .5:
                image = ImageOps.mirror(image)
            image = ImageEnhance.Brightness(image).enhance(random.uniform(.72, 1.28))
            image = ImageEnhance.Contrast(image).enhance(random.uniform(.75, 1.30))
        image = image.resize((IMAGE_SIZE, IMAGE_SIZE))
        tensor = torch.from_numpy(np.asarray(image).copy()).permute(2, 0, 1).float().div(255)
        return tensor, class_id


def evaluate(model: nn.Module, loader: DataLoader) -> dict[str, float]:
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for images, labels in loader:
            predictions = model(images).argmax(1)
            correct += int((predictions == labels).sum())
            total += int(labels.numel())
    return {"top1_accuracy": correct / total if total else 0.0, "samples": total}


parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--epochs", type=int, default=18)
parser.add_argument("--batch-size", type=int, default=32)
args = parser.parse_args()

train = ComponentCropDataset(args.dataset, "train", augment=True)
valid = ComponentCropDataset(args.dataset, "valid", augment=False)
counts = Counter(class_id for _, class_id, *_ in train.items)
weights = torch.tensor([1.0 / counts[class_id] for _, class_id, *_ in train.items], dtype=torch.double)
train_loader = DataLoader(train, batch_size=args.batch_size, sampler=WeightedRandomSampler(weights, len(weights), replacement=True), num_workers=0)
valid_loader = DataLoader(valid, batch_size=args.batch_size, shuffle=False, num_workers=0)
model = SnapshotClassifier(len(ELECTROCOM61_LABELS))
optimizer = torch.optim.AdamW(model.parameters(), lr=1.5e-3, weight_decay=2e-4)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
best_accuracy, best_state = 0.0, None
for epoch in range(1, args.epochs + 1):
    model.train(); loss_sum = 0.0
    for images, labels in train_loader:
        optimizer.zero_grad(set_to_none=True)
        loss = torch.nn.functional.cross_entropy(model(images), labels, label_smoothing=.05)
        loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 3.0); optimizer.step()
        loss_sum += float(loss)
    metrics = evaluate(model, valid_loader)
    scheduler.step()
    print(f"epoch={epoch}/{args.epochs} loss={loss_sum / len(train_loader):.4f} valid_top1={metrics['top1_accuracy']:.4f}")
    if metrics["top1_accuracy"] > best_accuracy:
        best_accuracy, best_state = metrics["top1_accuracy"], {key: value.cpu().clone() for key, value in model.state_dict().items()}

assert best_state is not None
model.load_state_dict(best_state); model.eval()
args.output.parent.mkdir(parents=True, exist_ok=True)
torch.jit.trace(model, torch.zeros(1, 3, IMAGE_SIZE, IMAGE_SIZE)).save(str(args.output))
args.output.with_suffix(".labels.json").write_text(json.dumps(ELECTROCOM61_LABELS, indent=2))
args.output.with_suffix(".evaluation.json").write_text(json.dumps({"dataset": "ElectroCom61 v2 CC BY 4.0", "validation": evaluate(model, valid_loader), "epochs": args.epochs, "train_crops": len(train), "valid_crops": len(valid), "usage": "review-only close-up snapshot component candidates"}, indent=2) + "\n")
