"""Local smoke test for the Circuit Lens FastAPI service.

Run from backend/ with: python scripts/check_api.py
"""
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


asset = Path(__file__).parents[2] / "frontend" / "public" / "assets" / "circuit-lens-live-board.png"
fixture = Path(__file__).parents[1] / "tests" / "fixtures" / "electrocom61" / "resistor-IMG20240417115121_jpg.rf.07f8811136cb87a39dabc9f7bbfadd0f.jpg"

with TestClient(app) as client:
    health = client.get("/health")
    assert health.status_code == 200, health.text
    assert health.json()["status"] == "ok", health.text

    catalog = client.get("/v1/catalog/resistor")
    assert catalog.status_code == 200, catalog.text
    assert catalog.json()["references"][0]["part_number"].startswith("CRCW0603"), catalog.text

    demo = client.get("/v1/detections/demo")
    assert demo.status_code == 200, demo.text
    assert len(demo.json()["detections"]) == 4, demo.text

    with asset.open("rb") as frame:
        inference = client.post("/v1/detections/infer", files={"image": (asset.name, frame, "image/png")})
    assert inference.status_code == 200, inference.text
    assert inference.json()["model_mode"] == "demo", inference.text

    with fixture.open("rb") as frame:
        real_data_inference = client.post("/v1/detections/infer", files={"image": (fixture.name, frame, "image/jpeg")})
    assert real_data_inference.status_code == 200, real_data_inference.text
    assert real_data_inference.json()["model_mode"] == "demo", real_data_inference.text

print("Circuit Lens backend smoke test passed.")
