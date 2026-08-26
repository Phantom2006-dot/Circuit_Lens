"""Circuit Lens FastAPI inference service."""
from __future__ import annotations

import io
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

from .board_classifier import create_board_classifier
from .boards import all_boards
from .catalog import all_references, references_for_family
from .contracts import DetectionResponse, HardwareConclusionResponse, TopologyAnalysisResponse
from .detector import create_detector, demo_detections
from .hardware import fuse_hardware_evidence
from .module_evidence import extract_module_markings
from .topology import analyze_topology


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.detector = create_detector()
    app.state.board_classifier = create_board_classifier()
    yield


allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]
app = FastAPI(title="Circuit Lens Inference API", version="1.6.0", lifespan=lifespan, description="PyTorch-ready circuit component detection service.")
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "model_mode": "torchscript" if app.state.detector else "demo", "board_model_mode": "torchscript" if app.state.board_classifier else "unavailable"}


@app.get("/v1/catalog")
async def catalog() -> dict[str, object]:
    return {"references": all_references()}


@app.get("/v1/catalog/{family}")
async def catalog_for_family(family: str) -> dict[str, object]:
    normalized = family.strip().replace("-", " ").title()
    records = references_for_family(normalized)
    if not records:
        raise HTTPException(status_code=404, detail="No component references found for this family.")
    return {"references": records}


@app.get("/v1/boards")
async def boards() -> dict[str, object]:
    return {"boards": all_boards()}


@app.get("/v1/detections/demo", response_model=DetectionResponse)
async def demo_pass() -> DetectionResponse:
    return DetectionResponse(detections=demo_detections(), model_mode="demo")


@app.post("/v1/detections/infer", response_model=DetectionResponse)
async def infer(image: UploadFile = File(...)) -> DetectionResponse:
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image.")
    raw = await image.read()
    if len(raw) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 12 MB or smaller.")
    try:
        decoded = Image.open(io.BytesIO(raw))
        decoded.verify()
        decoded = Image.open(io.BytesIO(raw)).convert("RGB")
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(status_code=400, detail="The upload could not be decoded as an image.") from error
    detector = app.state.detector
    if detector is None:
        return DetectionResponse(detections=demo_detections(), model_mode="demo")
    return DetectionResponse(detections=detector.detect(decoded), model_mode="torchscript")


@app.post("/v1/topology/analyze", response_model=TopologyAnalysisResponse)
async def topology_analyze(image: UploadFile = File(...)) -> TopologyAnalysisResponse:
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image.")
    raw = await image.read()
    if len(raw) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 12 MB or smaller.")
    try:
        decoded = Image.open(io.BytesIO(raw))
        decoded.verify()
        decoded = Image.open(io.BytesIO(raw)).convert("RGB")
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(status_code=400, detail="The upload could not be decoded as an image.") from error
    detector = app.state.detector
    detections = detector.detect(decoded) if detector else demo_detections()
    return analyze_topology(decoded, detections, "torchscript" if detector else "demo")


@app.post("/v1/hardware/identify", response_model=HardwareConclusionResponse)
async def identify_hardware(image: UploadFile = File(...)) -> HardwareConclusionResponse:
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image.")
    raw = await image.read()
    if len(raw) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 12 MB or smaller.")
    try:
        decoded = Image.open(io.BytesIO(raw))
        decoded.verify()
        decoded = Image.open(io.BytesIO(raw)).convert("RGB")
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(status_code=400, detail="The upload could not be decoded as an image.") from error
    detector = app.state.detector
    components = detector.detect(decoded) if detector else demo_detections()
    classifier = app.state.board_classifier
    predictions = classifier.classify(decoded) if classifier else []
    markings = extract_module_markings(decoded)
    return fuse_hardware_evidence(predictions, components, "torchscript" if classifier else "unavailable", markings)
