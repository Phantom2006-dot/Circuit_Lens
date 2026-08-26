# Snapshot Analysis and User Correction Design

## Purpose

The live view is useful for framing, but a still image gives Circuit Lens time to assess the complete board, preserve the evidence used for a result, and let the operator correct a missed identity. The native C++ client therefore adds a **Snapshot & Inspect** path and an **Open Image & Inspect** path.

| Action | Native C++ behavior | Evidence boundary |
| --- | --- | --- |
| Snapshot & Inspect | Copies the latest camera frame, saves a PNG, evaluates image quality, and runs the selected inspection mode against that immutable image. | A saved picture does not increase a model score. It makes the evidence reproducible. |
| Open Image & Inspect | Opens a JPEG, PNG, or WebP from disk and runs the same selected inspection mode. | This supports review of a photo even when no camera is attached. |
| Board outcome | Combines board classifier candidates, allowed OCR markings, catalog visual cues, source URL, and image-quality notes. | A board is named only if the existing confidence/margin or direct-marking gate passes. |
| Component outcome | Lists compact review-only candidates and any linked catalog reference. | It never asserts an exact part number or electrical value from the image alone. |
| User identification | Stores a user-entered label and snapshot reference in a local correction log. | It is explicitly marked **user-supplied, not model-verified**, and is never used as an automatic model result. |

## Local correction record

Each correction is appended as JSONL under the user’s writable application-data directory. The record contains the timestamp, active analysis mode, optional saved snapshot path, user-supplied label, and the displayed model outcome. This creates a reviewable data-collection queue for future labelled training, without silently treating a user’s phrase as a verified annotation.

> A user correction improves the inspection record immediately; it does not retrain or modify a model during a live session. Retraining requires curated images, bounding boxes where appropriate, validation, and an explicit model release.

## Quality guidance

The snapshot result includes resolution, median brightness, contrast, and a Laplacian-based blur indicator. The UI requests another picture when the board is too dark, washed out, soft, or too small for a legible silkscreen read. These are capture-quality observations, not electrical conclusions.
