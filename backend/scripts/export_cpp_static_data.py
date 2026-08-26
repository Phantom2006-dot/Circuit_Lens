"""Export Python catalog data into JSON assets consumed by the C++ inference service.

This is a one-time migration helper, not a runtime dependency of the C++ API.
"""
import json
from pathlib import Path

from app.boards import all_boards
from app.catalog import all_references


destination = Path(__file__).parents[2] / "backend-cpp" / "data"
destination.mkdir(parents=True, exist_ok=True)
(destination / "board_catalog.json").write_text(json.dumps(all_boards(), indent=2, ensure_ascii=False) + "\n")
(destination / "component_catalog.json").write_text(json.dumps(all_references(), indent=2, ensure_ascii=False) + "\n")
print(f"Exported C++ runtime catalogs to {destination}")
