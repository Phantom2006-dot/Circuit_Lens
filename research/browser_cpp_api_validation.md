# Browser-to-C++ API Validation Notes

The hosted Circuit Lens browser workspace loaded the new **Snapshot** and **Upload** controls. The native C++ service on port 8007 passed local health, multipart snapshot, and `OPTIONS` CORS checks with the published domain in `ALLOWED_ORIGINS`.

The public C++ health URL subsequently opened directly in the browser and returned both TorchScript model modes. The hosted Circuit Lens workspace also rendered the new **Snapshot** and **Upload** controls. A retried browser-context `fetch` to `/health` still returned `TypeError: Failed to fetch`; the collected browser console did not expose a separate CORS or CSP message. Direct navigation therefore works, but the current hosted browser context cannot be treated as able to call the exposed C++ endpoint until a same-origin or durable API deployment route is available.

The hosted Vite development server now proxies `/native-api/*` to the local native C++ service. Direct browser navigation to `/native-api/health` returned the TorchScript health payload, so the preview has a same-origin route suitable for browser integration testing. The refresh also showed the Snapshot and Upload controls in the workspace.

> Vite documents `server.proxy` as a **development-server** route facility: matching request paths are forwarded to the configured target. It is therefore appropriate for the hosted preview, but not a replacement for a production API deployment. [1]

A browser-context multipart call through `/native-api/v1/snapshot/inspect` succeeded and returned `snapshot_model_mode: torchscript` with three review-only candidates. The actual hidden Upload input was also exercised by dispatching a normal change event with the hosted demo-board image; the input accepted `browser-demo-board.png`. The remaining visual check is to confirm the asynchronous inspection card appears in the workspace after that event.

The snapshot card appeared in the hosted workspace after the upload event. It displayed the close-up ranking, review-only guidance, and the **Tell us what it is** correction input. A `Bench-verified test label` correction was submitted through the visible button, whose status changed to **Saved locally**. The UI did not convert the supplied correction into a model conclusion.

## Reference

[1] [Vite, “Server Options: server.proxy.”](https://vite.dev/config/server-options.html#server-proxy)
