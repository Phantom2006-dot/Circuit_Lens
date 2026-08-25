"""Conservative image-to-topology hypothesis builder for Circuit Lens.

This module never asserts an electrical truth from a single photograph. It turns
visible terminals and trace-like image evidence into an inspectable graph whose
links and patterns are explicitly marked for human review.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
from PIL import Image

from .contracts import CandidateLink, CandidateNet, CircuitDetection, CircuitPattern, TerminalEvidence, TopologyAnalysisResponse
from .taxonomy import terminal_count


def _terminal_positions(detection: CircuitDetection) -> list[tuple[float, float]]:
    box = detection.box
    count = min(terminal_count(detection.kind.replace(" ", "-")), 8)
    if count == 0:
        return []
    if count == 1:
        return [(box.x + box.width / 2, box.y + box.height / 2)]
    if count == 2:
        return [(box.x, box.y + box.height / 2), (box.x + box.width, box.y + box.height / 2)]
    if count == 3:
        return [(box.x, box.y + box.height * .25), (box.x, box.y + box.height * .75), (box.x + box.width, box.y + box.height / 2)]
    top = [(box.x + box.width * (index + 1) / (count // 2 + 1), box.y) for index in range(count // 2)]
    bottom = [(box.x + box.width * (index + 1) / (count - count // 2 + 1), box.y + box.height) for index in range(count - count // 2)]
    return top + bottom


def _trace_score(gray: np.ndarray, start: TerminalEvidence, end: TerminalEvidence) -> float:
    height, width = gray.shape
    samples = max(12, int(np.hypot(end.x - start.x, end.y - start.y)))
    xs = np.linspace(start.x / 100 * (width - 1), end.x / 100 * (width - 1), samples).astype(int)
    ys = np.linspace(start.y / 100 * (height - 1), end.y / 100 * (height - 1), samples).astype(int)
    values = gray[np.clip(ys, 0, height - 1), np.clip(xs, 0, width - 1)]
    local_contrast = np.abs(np.diff(values.astype(float))).mean() / 255 if len(values) > 1 else 0
    darkness = 1 - values.mean() / 255
    # Dark or high-contrast continuous paths are only visual evidence, not a net.
    return float(np.clip(.48 * darkness + .52 * local_contrast + .10, 0, 1))


def _connected_components(terminals: list[TerminalEvidence], links: list[CandidateLink]) -> list[CandidateNet]:
    parent = {terminal.id: terminal.id for terminal in terminals}
    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node
    def union(left: str, right: str) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left
    for link in links:
        union(link.source_terminal, link.target_terminal)
    buckets: dict[str, list[str]] = {}
    for terminal in terminals:
        buckets.setdefault(find(terminal.id), []).append(terminal.id)
    return [CandidateNet(id=f"net-{index + 1}", terminal_ids=terminal_ids, confidence=round(min((link.confidence for link in links if link.source_terminal in terminal_ids and link.target_terminal in terminal_ids), default=.2), 3), requires_review=True) for index, terminal_ids in enumerate(buckets.values()) if len(terminal_ids) > 1]


def _pattern_hypotheses(detections: list[CircuitDetection], links: list[CandidateLink]) -> list[CircuitPattern]:
    kinds = {detection.kind for detection in detections}
    patterns: list[CircuitPattern] = []
    if {"BJT Transistor", "Diode"}.issubset(kinds) or {"MOSFET", "Diode"}.issubset(kinds):
        patterns.append(CircuitPattern(label="Switching or driver stage candidate", confidence=.34, evidence=["A transistor-family and diode-family candidate are present.", f"{len(links)} visual terminal links survived the conservative gate."], requires_review=True))
    if any("Capacitor" in kind for kind in kinds) and any(kind in kinds for kind in {"Buck Converter", "1 5 Volt Battery", "3 3 Volt Battery", "9 Volt Battery"}):
        patterns.append(CircuitPattern(label="Power filtering or conversion candidate", confidence=.31, evidence=["A capacitor-family and power-family candidate are visible."], requires_review=True))
    if any(kind in kinds for kind in {"Arduino Nano", "Arduino Uno", "Arduino Mega", "ESP32", "ESP32 CAM"}):
        patterns.append(CircuitPattern(label="Controller subsystem candidate", confidence=.42, evidence=["A controller-module candidate is visible; surrounding links require a board-level view."], requires_review=True))
    if not patterns:
        patterns.append(CircuitPattern(label="Unclassified circuit region", confidence=.10, evidence=["Visible component and trace evidence is insufficient to classify a circuit function."], requires_review=True))
    return patterns


def analyze_topology(image: Image.Image, detections: list[CircuitDetection], model_mode: str) -> TopologyAnalysisResponse:
    gray = np.asarray(image.convert("L").resize((640, 640)))
    terminals: list[TerminalEvidence] = []
    for detection in detections:
        for index, (x, y) in enumerate(_terminal_positions(detection)):
            terminals.append(TerminalEvidence(id=f"{detection.id}:p{index + 1}", component_id=detection.id, x=round(x, 2), y=round(y, 2), confidence=round(detection.confidence * .65, 3)))
    links: list[CandidateLink] = []
    for start, end in combinations(terminals, 2):
        if start.component_id == end.component_id:
            continue
        distance = np.hypot(start.x - end.x, start.y - end.y)
        if distance > 45:
            continue
        score = _trace_score(gray, start, end)
        if score >= .43:
            links.append(CandidateLink(source_terminal=start.id, target_terminal=end.id, confidence=round(score, 3), evidence=["Terminal geometry is within the candidate search radius.", "Pixel-path contrast produced trace-like visual evidence."], requires_review=True))
    links = sorted(links, key=lambda item: item.confidence, reverse=True)[:24]
    return TopologyAnalysisResponse(detections=detections, terminals=terminals, candidate_links=links, candidate_nets=_connected_components(terminals, links), candidate_patterns=_pattern_hypotheses(detections, links), limitations=["A single optical view cannot reveal hidden, covered, inner-layer, or solder-mask-obscured traces.", "All terminal links and pattern labels are visual hypotheses that require a TOP/BOTTOM image pair, continuity testing, and engineering review.", "The current bundled model is a review-only baseline; broad 61-class recognition requires training and calibration before deployment."], model_mode=model_mode)
