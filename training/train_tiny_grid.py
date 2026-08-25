"""Train Circuit Lens's compact PyTorch baseline on real ElectroCom61 labels.

Example (quick verification on CPU):
  python train_tiny_grid.py --dataset data/electrocom61 --output models/tiny-grid.pt --epochs 1 --max-samples 64

For a meaningful baseline, omit --max-samples and train/evaluate on the complete
ElectroCom61 split. This model is intentionally compact; it is a reproducible
baseline rather than a production-accuracy claim.
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset

from electrocom61 import CANONICAL_FAMILIES, image_label_pairs, target_class_map

import sys
sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))
from app.tiny_grid import GRID_SIZE, INPUT_SIZE, TinyGridDetector  # noqa: E402


class ElectroCom61FourFamilyDataset(Dataset):
    def __init__(self, root: Path, split: str, max_samples: int | None = None) -> None:
        mapping = target_class_map(root)
        self.items = list(image_label_pairs(root, split, mapping))
        if max_samples:
            self.items = self.items[:max_samples]

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int):
        image_path, labels = self.items[index]
        image = Image.open(image_path).convert("RGB").resize((INPUT_SIZE, INPUT_SIZE))
        image_tensor = torch.from_numpy(__import__("numpy").asarray(image).copy()).permute(2, 0, 1).float().div(255)
        target = torch.zeros((5 + len(CANONICAL_FAMILIES), GRID_SIZE, GRID_SIZE), dtype=torch.float32)
        for family_index, cx, cy, width, height in labels:
            column, row = min(GRID_SIZE - 1, int(cx * GRID_SIZE)), min(GRID_SIZE - 1, int(cy * GRID_SIZE))
            target[0, row, column] = 1
            target[1, row, column] = cx * GRID_SIZE - column
            target[2, row, column] = cy * GRID_SIZE - row
            target[3, row, column] = min(0.999, width / 0.36)
            target[4, row, column] = min(0.999, height / 0.36)
            target[5 + family_index, row, column] = 1
        return image_tensor, target


def loss_fn(prediction: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    positive_weight = torch.tensor(25.0, dtype=prediction.dtype, device=prediction.device)
    objectness = F.binary_cross_entropy_with_logits(prediction[:, 0], target[:, 0], pos_weight=positive_weight)
    positive = target[:, 0].bool()
    if not positive.any():
        return objectness
    box = F.smooth_l1_loss(torch.sigmoid(prediction[:, 1:5]).permute(0, 2, 3, 1)[positive], target[:, 1:5].permute(0, 2, 3, 1)[positive])
    labels = target[:, 5:].argmax(dim=1)
    class_loss = F.cross_entropy(prediction[:, 5:], labels, reduction="none")[positive].mean()
    return objectness + 2.0 * box + class_loss


parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--epochs", type=int, default=12)
parser.add_argument("--batch-size", type=int, default=8)
parser.add_argument("--learning-rate", type=float, default=1e-3)
parser.add_argument("--max-samples", type=int)
parser.add_argument("--seed", type=int, default=61)
args = parser.parse_args()

random.seed(args.seed)
torch.manual_seed(args.seed)
dataset = ElectroCom61FourFamilyDataset(args.dataset, "train", args.max_samples)
if not dataset:
    raise SystemExit("No mapped ElectroCom61 images were found.")
loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
model = TinyGridDetector(num_classes=len(CANONICAL_FAMILIES))
optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
model.train()
for epoch in range(args.epochs):
    total = 0.0
    for images, targets in loader:
        optimizer.zero_grad(set_to_none=True)
        loss = loss_fn(model(images), targets)
        loss.backward()
        optimizer.step()
        total += float(loss)
    print(f"epoch={epoch + 1}/{args.epochs} loss={total / len(loader):.4f}")

args.output.parent.mkdir(parents=True, exist_ok=True)
model.eval()
traced = torch.jit.trace(model, torch.zeros(1, 3, INPUT_SIZE, INPUT_SIZE))
traced.save(str(args.output))
print(f"Saved TorchScript model to {args.output}")
