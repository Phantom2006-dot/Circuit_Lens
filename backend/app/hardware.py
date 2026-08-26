"""Evidence fusion for joint board and component identification."""
from __future__ import annotations

from .board_classifier import BoardPrediction
from .boards import board_by_id
from .contracts import BoardMatch, CircuitDetection, HardwareConclusionResponse
from .module_evidence import board_from_direct_marking, markings_for_board


COMPONENT_HINTS = {
    "esp32_dev_board": ("ESP32", "Bluetooth Module"),
    "esp32_cam": ("ESP32 CAM", "Camera", "OV2640"),
    "arduino_uno_r3": ("ATmega",),
    "arduino_nano": ("ATmega",),
    "arduino_mega_2560": ("ATmega",),
    "jetson_nano": ("Jetson",),
    "jetson_tx2": ("Jetson",),
}


def _component_support(board_id: str, detections: list[CircuitDetection]) -> list[str]:
    kinds = " ".join(detection.kind for detection in detections).lower()
    return [hint for hint in COMPONENT_HINTS.get(board_id, ()) if hint.lower() in kinds]


def fuse_hardware_evidence(predictions: list[BoardPrediction], detections: list[CircuitDetection], board_model_mode: str, markings: list[str] | None = None) -> HardwareConclusionResponse:
    markings = markings or []
    prediction_scores = {prediction.board_id: prediction.confidence for prediction in predictions}
    direct_marking_board = board_from_direct_marking(markings)
    if direct_marking_board:
        prediction_scores[direct_marking_board] = 0.99
    matches: list[BoardMatch] = []
    for board_id, classifier_confidence in prediction_scores.items():
        board = board_by_id(board_id)
        if not board:
            continue
        supporting = _component_support(board.id, detections)
        marking_support = markings_for_board(board.id, markings)
        fused = min(0.99, classifier_confidence + min(.10, .04 * len(supporting)) + (0.04 if marking_support else 0))
        matches.append(BoardMatch(board_id=board.id, name=board.name, family=board.family, confidence=round(fused, 4), supported_by_trained_model=board.supported_by_trained_model, component_evidence=supporting, marking_evidence=marking_support, visual_evidence=list(board.visual_cues), source_url=board.source_url))
    matches.sort(key=lambda match: match.confidence, reverse=True)
    top, runner_up = (matches[0] if matches else None), (matches[1] if len(matches) > 1 else None)
    margin = (top.confidence - runner_up.confidence) if top and runner_up else (top.confidence if top else 0)
    model_gate = bool(top and top.supported_by_trained_model and top.confidence >= .70 and margin >= .12)
    marking_gate = bool(top and top.board_id == direct_marking_board and len(top.marking_evidence) > 0)
    gate_passes = model_gate or marking_gate
    conclusion = top.name if gate_passes else "No reliable board conclusion from this frame"
    status = "candidate_conclusion" if gate_passes else "needs_more_evidence"
    evidence = []
    if top:
        if top.board_id == direct_marking_board and top.marking_evidence:
            evidence.append(f"Direct silkscreen signature identifies: {top.name}.")
        else:
            evidence.append(f"Board classifier top prediction: {top.name} at {top.confidence:.0%}.")
        evidence.extend(f"Silkscreen marking read: {marking}." for marking in top.marking_evidence)
        evidence.extend(f"Visual cue expected: {cue}." for cue in top.visual_evidence[:2])
        evidence.extend(f"Component clue found: {hint}." for hint in top.component_evidence)
    if not gate_passes:
        evidence.append("The confidence/margin gate did not support a reliable conclusion; capture a wider, sharper board view with silkscreen and connectors visible.")
    return HardwareConclusionResponse(components=detections, board_matches=matches, conclusion=conclusion, conclusion_status=status, evidence=evidence, recognized_markings=markings, next_capture="Capture the entire front side, then the back side; keep USB, camera, RF, header, and silkscreen regions in view. Use a continuity test for electrical claims.", board_model_mode=board_model_mode)
