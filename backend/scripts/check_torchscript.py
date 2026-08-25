"""Exercise the real-data ElectroCom61 TorchScript baseline through FastAPI.

Run from backend/ with:
  PYTHONPATH=. python scripts/check_torchscript.py
"""
import os
from pathlib import Path

model = Path(__file__).parents[1] / "models" / "electrocom61-tiny-grid-baseline.pt"
os.environ["MODEL_PATH"] = str(model)
os.environ["CONFIDENCE_THRESHOLD"] = "0.20"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


fixture_dir = Path(__file__).parents[1] / "tests" / "fixtures" / "electrocom61"
with TestClient(app) as client:
    health = client.get("/health")
    assert health.status_code == 200, health.text
    assert health.json()["model_mode"] == "torchscript", health.text

    for fixture in sorted(fixture_dir.glob("*.jpg")):
        with fixture.open("rb") as frame:
            response = client.post("/v1/detections/infer", files={"image": (fixture.name, frame, "image/jpeg")})
        assert response.status_code == 200, response.text
        assert response.json()["model_mode"] == "torchscript", response.text
        print(f"{fixture.name}: {len(response.json()['detections'])} candidate(s)")

print("Circuit Lens TorchScript smoke test passed.")
