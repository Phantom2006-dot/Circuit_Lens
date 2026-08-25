"""Train a compact TorchScript development-board classifier on IoTKITs crops."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from board_model import BoardClassifier, IMAGE_SIZE


class BoardDataset(Dataset):
    def __init__(self, root: Path, labels: list[str]) -> None:
        self.items = [(path, labels.index(path.parent.name)) for label in labels for path in sorted((root / label).glob("*.jpg"))]
    def __len__(self) -> int: return len(self.items)
    def __getitem__(self, index: int):
        path, label = self.items[index]
        image = Image.open(path).convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE))
        array = np.asarray(image).copy()
        return torch.from_numpy(array).permute(2, 0, 1).float().div(255), label


parser = argparse.ArgumentParser()
parser.add_argument("--crops", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--epochs", type=int, default=15)
args = parser.parse_args()
labels = sorted(path.name for path in (args.crops / "train").iterdir() if path.is_dir())
train, valid = BoardDataset(args.crops / "train", labels), BoardDataset(args.crops / "valid", labels)
class_counts = torch.tensor([sum(label == index for _, label in train.items) for index in range(len(labels))], dtype=torch.float)
weights = [1 / class_counts[label].item() for _, label in train.items]
loader = DataLoader(train, batch_size=24, sampler=WeightedRandomSampler(weights, len(weights), replacement=True))
model = BoardClassifier(len(labels))
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
for epoch in range(args.epochs):
    model.train(); running = 0.0
    for images, targets in loader:
        optimizer.zero_grad(set_to_none=True); current = nn.functional.cross_entropy(model(images), targets); current.backward(); optimizer.step(); running += float(current)
    model.eval(); correct = 0
    with torch.no_grad():
        for image, target in valid:
            correct += int(model(image.unsqueeze(0)).argmax(1).item() == target)
    print(f"epoch={epoch + 1}/{args.epochs} loss={running / len(loader):.4f} valid_accuracy={correct / max(1, len(valid)):.3f}")
args.output.parent.mkdir(parents=True, exist_ok=True)
model.eval(); torch.jit.trace(model, torch.zeros(1, 3, IMAGE_SIZE, IMAGE_SIZE)).save(str(args.output))
args.output.with_suffix(".labels.json").write_text(json.dumps(labels, indent=2))
