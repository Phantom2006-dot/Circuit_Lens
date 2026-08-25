# Temporary Preview Verification

The hosted Circuit Lens preview loaded the updated interface and displayed the ElectroCom61 baseline integration code. The temporary FastAPI endpoint at `/health` returned `{"status":"ok","model_mode":"torchscript"}` before the frontend test.

The sandbox browser was unable to grant a physical camera stream, so selecting **Arm camera** correctly transitioned the page to its **Camera blocked** state and preserved the demo feed. This verifies the permission-failure path, but not a physical-frame upload from the sandbox browser. The backend upload and TorchScript path were separately validated against real ElectroCom61 fixture images through FastAPI smoke tests.

After the orientation and topology update, the hosted preview displayed the **Analyze topology** control. The browser successfully fetched the replacement topology API across origins; `/health` returned `{"status":"ok","model_mode":"torchscript"}`. A sandbox camera stream was still unavailable, so topology analysis was validated separately through the real ElectroCom61 fixture smoke test rather than a browser camera frame.

After the smart-vision update, the hosted preview displayed both **Conclude hardware** and **Analyze topology**. The browser successfully reached the unified API across origins; `/health` returned `{"status":"ok","model_mode":"torchscript","board_model_mode":"torchscript"}`. The physical camera limitation in the sandbox remains, so live-frame behavior is validated through API fixture requests and must be exercised on a real device for camera-specific testing.

After the expanded marked-object update, the hosted preview displayed **All**, **Passives**, **Semiconductors**, **Power**, **Connectors**, **Modules**, **Sensors**, **Switches & motion**, **Displays**, and **Other**, plus a marked-object search field. The browser successfully reached the calibrated full-vocabulary service across origins; `/health` again reported both `model_mode` and `board_model_mode` as `torchscript`.
