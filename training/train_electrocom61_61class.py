"""Train a 61-class TinyGrid baseline on all original ElectroCom61 labels.

This preserves the source class vocabulary and writes a TorchScript model plus a
label sidecar, which the API loads using MODEL_PATH and MODEL_LABELS_PATH.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from PIL import Image
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))
from app.tiny_grid import GRID_SIZE, INPUT_SIZE, TinyGridDetector  # noqa: E402
from electrocom61 import dataset_names  # noqa: E402


class FullElectroComDataset(Dataset):
    def __init__(self, root: Path, split: str, names: list[str]) -> None:
        self.names, self.items = names, []
        for image_path in sorted((root / split / "images").glob("*")):
            label_path = root / split / "labels" / f"{image_path.stem}.txt"
            if label_path.exists():
                labels = [list(map(float, row.split())) for row in label_path.read_text().splitlines() if len(row.split()) == 5]
                if labels:
                    self.items.append((image_path, labels))
    def __len__(self) -> int: return len(self.items)
    def __getitem__(self, index: int):
        image_path, labels = self.items[index]
        image = Image.open(image_path).convert("RGB").resize((INPUT_SIZE, INPUT_SIZE))
        image_tensor = torch.from_numpy(__import__("numpy").asarray(image).copy()).permute(2, 0, 1).float().div(255)
        target = torch.zeros((5 + len(self.names), GRID_SIZE, GRID_SIZE))
        for class_id, cx, cy, width, height in labels:
            row, column = min(GRID_SIZE - 1, int(cy * GRID_SIZE)), min(GRID_SIZE - 1, int(cx * GRID_SIZE))
            target[0, row, column], target[1, row, column], target[2, row, column] = 1, cx * GRID_SIZE - column, cy * GRID_SIZE - row
            target[3, row, column], target[4, row, column], target[5 + int(class_id), row, column] = min(.999, width / .36), min(.999, height / .36), 1
        return image_tensor, target


def loss(prediction: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    positive = target[:, 0].bool()
    objectness = F.binary_cross_entropy_with_logits(prediction[:, 0], target[:, 0], pos_weight=torch.tensor(25.0, device=prediction.device))
    if not positive.any(): return objectness
    boxes = F.smooth_l1_loss(torch.sigmoid(prediction[:, 1:5]).permute(0, 2, 3, 1)[positive], target[:, 1:5].permute(0, 2, 3, 1)[positive])
    classes = F.cross_entropy(prediction[:, 5:], target[:, 5:].argmax(1), reduction="none")[positive].mean()
    return objectness + 2 * boxes + classes


parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--epochs", type=int, default=30)
parser.add_argument("--batch-size", type=int, default=8)
args = parser.parse_args()
names = dataset_names(args.dataset)
dataset = FullElectroComDataset(args.dataset, "train", names)
loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
model = TinyGridDetector(num_classes=len(names))
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
for epoch in range(args.epochs):
    running = 0.0
    for images, targets in loader:
        optimizer.zero_grad(set_to_none=True); current = loss(model(images), targets); current.backward(); optimizer.step(); running += float(current)
    print(f"epoch={epoch + 1}/{args.epochs} loss={running / len(loader):.4f}")
args.output.parent.mkdir(parents=True, exist_ok=True)
model.eval(); torch.jit.trace(model, torch.zeros(1, 3, INPUT_SIZE, INPUT_SIZE)).save(str(args.output))
args.output.with_suffix(".labels.json").write_text(json.dumps(names, indent=2))
