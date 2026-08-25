"""Smoke test the joint board-and-component conclusion endpoint on a real IoTKITs image."""
import os
from pathlib import Path

backend = Path(__file__).parents[1]
os.environ.update({
    "MODEL_PATH": str(backend / "models" / "electrocom61-tiny-grid-baseline.pt"),
    "MODEL_LABELS_PATH": str(backend / "models" / "electrocom61-tiny-grid-baseline.labels.json"),
    "CONFIDENCE_THRESHOLD": "0.20",
    "BOARD_MODEL_PATH": str(backend / "models" / "iotkits-board-classifier.pt"),
    "BOARD_MODEL_LABELS_PATH": str(backend / "models" / "iotkits-board-classifier.labels.json"),
})

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

image = next((Path(__file__).parents[2] / "training" / "data" / "iotkits" / "valid").glob("*.jpg"))
with TestClient(app) as client:
    with image.open("rb") as payload:
        response = client.post("/v1/hardware/identify", files={"image": (image.name, payload, "image/jpeg")})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["board_model_mode"] == "torchscript", result
    assert result["board_matches"], result
    assert "components" in result and "conclusion" in result, result
    print(f"Hardware endpoint passed: {result['conclusion_status']}; top={result['board_matches'][0]['name']} ({result['board_matches'][0]['confidence']:.0%}); components={len(result['components'])}")
