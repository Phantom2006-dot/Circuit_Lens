"""ElectroCom61 data utilities for Circuit Lens.

The public CC BY 4.0 ElectroCom61 v2 dataset uses YOLO labels for 61 electronic
component classes. Circuit Lens initially trains a practical four-family model:
Resistor, Transistor (BJT, MOSFET, IGBT), Diode (including Zener), and Capacitor
(electrolytic, film, ceramic, and MLCC variants).
"""
from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path
from typing import Iterable


CANONICAL_FAMILIES = ["Resistor", "Transistor", "Diode", "Capacitor"]
CLASS_TO_FAMILY = {
    "Resistor": "Resistor",
    "BJT-Transistor": "Transistor",
    "MOSFET": "Transistor",
    "IGBT": "Transistor",
    "Diode": "Diode",
    "Zener-Diode": "Diode",
    "Capacitor-10mf": "Capacitor",
    "Capacitor-470mf": "Capacitor",
    "Film-Capacitor": "Capacitor",
    "High-Voltage-Ceramic-Capacitor": "Capacitor",
    "Low-Voltage-Ceramic-Capacitor": "Capacitor",
    "MLC-Capacitor": "Capacitor",
}


def dataset_names(dataset_root: Path) -> list[str]:
    """Load the ElectroCom61 class order without executing any dataset code."""
    for line in (dataset_root / "data.yaml").read_text(encoding="utf-8").splitlines():
        if line.startswith("names:"):
            return list(ast.literal_eval(line.split(":", 1)[1].strip()))
    raise ValueError("ElectroCom61 data.yaml has no names list.")


def target_class_map(dataset_root: Path) -> dict[int, int]:
    names = dataset_names(dataset_root)
    mapping: dict[int, int] = {}
    for source_index, name in enumerate(names):
        family = CLASS_TO_FAMILY.get(name)
        if family:
            mapping[source_index] = CANONICAL_FAMILIES.index(family)
    return mapping


def yolo_labels(label_path: Path, relevant_classes: dict[int, int]) -> list[tuple[int, float, float, float, float]]:
    labels: list[tuple[int, float, float, float, float]] = []
    for raw_line in label_path.read_text(encoding="utf-8").splitlines():
        parts = raw_line.split()
        if len(parts) != 5:
            continue
        source_class, center_x, center_y, width, height = map(float, parts)
        source_index = int(source_class)
        if source_index in relevant_classes:
            labels.append((relevant_classes[source_index], center_x, center_y, width, height))
    return labels


def image_label_pairs(dataset_root: Path, split: str, relevant_classes: dict[int, int]) -> Iterable[tuple[Path, list[tuple[int, float, float, float, float]]]]:
    image_dir = dataset_root / split / "images"
    label_dir = dataset_root / split / "labels"
    for image_path in sorted(image_dir.glob("*")):
        label_path = label_dir / f"{image_path.stem}.txt"
        if not label_path.exists():
            continue
        labels = yolo_labels(label_path, relevant_classes)
        if labels:
            yield image_path, labels


def family_counts(dataset_root: Path) -> dict[str, int]:
    mapping = target_class_map(dataset_root)
    counts: Counter[str] = Counter()
    for split in ("train", "valid", "test"):
        for _, labels in image_label_pairs(dataset_root, split, mapping):
            for family_index, *_ in labels:
                counts[CANONICAL_FAMILIES[family_index]] += 1
    return dict(counts)
