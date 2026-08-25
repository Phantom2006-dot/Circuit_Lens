"""API contracts for visual component detection and conservative topology hypotheses."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    width: float = Field(gt=0, le=100)
    height: float = Field(gt=0, le=100)


class CircuitDetection(BaseModel):
    id: str
    kind: str
    family: str
    ref: str
    confidence: float = Field(ge=0, le=1)
    health: Literal["Verified", "Likely", "Review"]
    box: BoundingBox
    value: str
    note: str


class DetectionResponse(BaseModel):
    detections: list[CircuitDetection]
    model_mode: Literal["demo", "torchscript"]


class TerminalEvidence(BaseModel):
    id: str
    component_id: str
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)


class CandidateLink(BaseModel):
    source_terminal: str
    target_terminal: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]
    requires_review: bool = True


class CandidateNet(BaseModel):
    id: str
    terminal_ids: list[str]
    confidence: float = Field(ge=0, le=1)
    requires_review: bool = True


class CircuitPattern(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]
    requires_review: bool = True


class TopologyAnalysisResponse(BaseModel):
    detections: list[CircuitDetection]
    terminals: list[TerminalEvidence]
    candidate_links: list[CandidateLink]
    candidate_nets: list[CandidateNet]
    candidate_patterns: list[CircuitPattern]
    limitations: list[str]
    model_mode: Literal["demo", "torchscript"]


class BoardMatch(BaseModel):
    board_id: str
    name: str
    family: str
    confidence: float = Field(ge=0, le=1)
    supported_by_trained_model: bool
    component_evidence: list[str]
    visual_evidence: list[str]
    source_url: str


class HardwareConclusionResponse(BaseModel):
    components: list[CircuitDetection]
    board_matches: list[BoardMatch]
    conclusion: str
    conclusion_status: Literal["candidate_conclusion", "needs_more_evidence"]
    evidence: list[str]
    next_capture: str
    board_model_mode: Literal["unavailable", "torchscript"]
