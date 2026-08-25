# Circuit Lens v1.6 — Deployment Package

For a complete description of the real ElectroCom61 data path, PyTorch baseline, camera-frame sampling, actual local test results, and production limitations, read [TECHNICAL_IMPLEMENTATION.md](./TECHNICAL_IMPLEMENTATION.md).

For the camera-orientation correction, full ElectroCom61 taxonomy, circuit-topology endpoint, validation evidence, and limitations of the new graph-analysis feature, read [CIRCUIT_TOPOLOGY_CHANGE_NOTE.md](./CIRCUIT_TOPOLOGY_CHANGE_NOTE.md).

For the full marked-object vocabulary, component-and-board evidence fusion, model measurements, and remaining validation limits, read [SMART_PERCEPTION_CHANGE_NOTE.md](./SMART_PERCEPTION_CHANGE_NOTE.md).

This package separates Circuit Lens into two deployable applications. The **frontend** is a Vite/React single-page application for Vercel, while the **backend** is a FastAPI service for Fly.io. The browser never holds a PyTorch model or deployment secret. It reads the public `VITE_API_BASE_URL` at build time and calls the Fly.io service for deterministic demonstration data or uploaded-frame inference.

| Directory | Responsibility | Deployment target |
| --- | --- | --- |
| `frontend/` | React interface, camera permission flow, component overlays, static assets, and API client | Vercel |
| `backend/` | CORS-restricted FastAPI endpoints, image validation, demonstration adapter, and TorchScript model adapter | Fly.io |

## Local development

Run the backend first. Create a local environment using the values in `backend/env.template`, set `ALLOWED_ORIGINS` to include `http://localhost:5173`, install the requirements, and start the service with `uvicorn app.main:app --reload --port 8080` from the `backend/` directory.

Then configure `VITE_API_BASE_URL=http://localhost:8080` using `frontend/env.template`, run `pnpm install`, and run `pnpm dev` from `frontend/`. With no model mounted, the API returns deterministic demonstration detections so the entire interface remains testable before model training is complete.

## Deploy the backend to Fly.io

The `backend/Dockerfile` packages the FastAPI service and exposes port `8080`. From `backend/`, install and authenticate the Fly.io CLI, run `fly launch` to reserve a unique app name, update the `app` value in `fly.toml` if Fly changes it, configure `ALLOWED_ORIGINS` using your Vercel URL, and run `fly deploy`. Fly.io’s FastAPI guide uses this container-first workflow, and its `fly.toml` configuration controls the app name, Docker build, exposed HTTP service, and runtime environment.[1] [2]

The provided configuration allows the service to stop when idle to reduce cost. For live field use, change `auto_stop_machines` to `"off"` and `min_machines_running` to `1`; that keeps the model process warm but costs more. Any value in `fly.toml` is public configuration; use Fly.io secrets for sensitive values instead of committing them.[2]

## Deploy the frontend to Vercel

Import the `frontend/` directory as the Vercel project root. Vercel detects Vite and uses the `build` script to produce the static production bundle. In the Vercel Environment Variables page, set `VITE_API_BASE_URL` to the deployed Fly URL, for example `https://your-circuit-lens-api.fly.dev`, then redeploy. Vite variables that must be readable in browser code use the `VITE_` prefix.[3]

`vercel.json` includes the SPA fallback rewrite so direct navigation to a client route resolves to `index.html`, consistent with Vercel’s Vite SPA guidance.[3] Add a custom domain later in Vercel’s project domain settings, then update `ALLOWED_ORIGINS` on Fly.io to include that exact `https://` origin.

## Models and data coverage

The package now includes two TorchScript artifacts: the ElectroCom61-derived **61-class component candidate model** configured through `MODEL_PATH` and the IoTKITs-derived **15-class board classifier** configured through `BOARD_MODEL_PATH`. The component adapter uses a grid-based output with class labels held in the matching JSON sidecar; the board classifier returns ranked board identities. The API fuses the two evidence streams but preserves broad component predictions as review-only candidates.

The model file is ignored by Docker by default. For experiments, remove the model exclusion in `.dockerignore` and copy the model into the image. For production, use controlled model downloading or object storage with a startup integrity check; do not add private model weights to the frontend repository.

## Current prototype boundary

The UI and API are working software with sampled camera-frame upload, a trained component candidate model, and a trained board classifier. However, the broad component baseline has not met the accuracy required for verified identification; its candidates must be confirmed using markings, package geometry, schematic/BOM evidence, and—where applicable—electrical measurements. `inferCircuitImage()` is ready for a canvas frame or a React Native camera adapter, and the backend validates JPEG, PNG, and WebP uploads before applying the models.

> Manus hosting remains available as a built-in alternative with custom-domain support. This package follows your requested Vercel and Fly.io split, so you can deploy each layer independently.

## References

[1] [Fly.io, “Run a FastAPI app.”](https://fly.io/docs/python/frameworks/fastapi/)

[2] [Fly.io, “App configuration (fly.toml).”](https://fly.io/docs/reference/configuration/)

[3] [Vercel, “Vite on Vercel.”](https://vercel.com/docs/frameworks/frontend/vite)
