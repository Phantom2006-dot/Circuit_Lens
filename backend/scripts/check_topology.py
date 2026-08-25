"""Exercise the topology-hypothesis endpoint with a real ElectroCom61 image."""
import os
from pathlib import Path

model = Path(__file__).parents[1] / "models" / "electrocom61-tiny-grid-baseline.pt"
labels = Path(__file__).parents[1] / "models" / "electrocom61-tiny-grid-baseline.labels.json"
os.environ["MODEL_PATH"] = str(model)
os.environ["MODEL_LABELS_PATH"] = str(labels)
os.environ["CONFIDENCE_THRESHOLD"] = "0.20"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

fixture = Path(__file__).parents[1] / "tests" / "fixtures" / "electrocom61" / "resistor-IMG20240417115121_jpg.rf.07f8811136cb87a39dabc9f7bbfadd0f.jpg"
with TestClient(app) as client:
    with fixture.open("rb") as image:
        response = client.post("/v1/topology/analyze", files={"image": (fixture.name, image, "image/jpeg")})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["model_mode"] == "torchscript", payload
    assert "candidate_patterns" in payload and "limitations" in payload, payload
    print(f"Topology endpoint passed: {len(payload['detections'])} candidates, {len(payload['terminals'])} terminals, {len(payload['candidate_links'])} review links.")
