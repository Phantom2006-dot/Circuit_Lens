"""Small PyTorch detector used for repeatable component-recognition baselines."""
from __future__ import annotations

import torch
from torch import nn

from .taxonomy import ELECTROCOM61_LABELS

CLASS_NAMES = ELECTROCOM61_LABELS
INPUT_SIZE = 256
GRID_SIZE = 16


class TinyGridDetector(nn.Module):
    def __init__(self, num_classes: int = len(CLASS_NAMES)) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 24, 3, stride=2, padding=1), nn.BatchNorm2d(24), nn.SiLU(),
            nn.Conv2d(24, 48, 3, stride=2, padding=1), nn.BatchNorm2d(48), nn.SiLU(),
            nn.Conv2d(48, 96, 3, stride=2, padding=1), nn.BatchNorm2d(96), nn.SiLU(),
            nn.Conv2d(96, 128, 3, stride=2, padding=1), nn.BatchNorm2d(128), nn.SiLU(),
        )
        self.head = nn.Conv2d(128, 5 + num_classes, kernel_size=1)

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        return self.head(self.features(image))
