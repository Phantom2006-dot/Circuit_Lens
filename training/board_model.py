"""Shared compact CNN definition for IoTKITs board classification."""
from __future__ import annotations

import torch
from torch import nn


IMAGE_SIZE = 160


class BoardClassifier(nn.Module):
    def __init__(self, classes: int) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, 2, 1), nn.BatchNorm2d(32), nn.SiLU(),
            nn.Conv2d(32, 64, 3, 2, 1), nn.BatchNorm2d(64), nn.SiLU(),
            nn.Conv2d(64, 128, 3, 2, 1), nn.BatchNorm2d(128), nn.SiLU(),
            nn.Conv2d(128, 192, 3, 2, 1), nn.BatchNorm2d(192), nn.SiLU(), nn.AdaptiveAvgPool2d(1),
        )
        self.classifier = nn.Linear(192, classes)
    def forward(self, image: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(image).flatten(1))
