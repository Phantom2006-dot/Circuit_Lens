# Hosted Preview Validation — Module Recognition Release

**Date:** 2026-08-26

The hosted Circuit Lens preview was opened successfully after connecting it to the marking-aware FastAPI service. The interface exposes exactly two analysis choices: **Analyze components** and **Identify circuit board**. Switching to board mode changes the page heading, primary action, video status, and inference-pass label to the board-identification workflow.

The public preview origin received `Access-Control-Allow-Origin` from the temporary API, whose health endpoint reported both the component and board models as `torchscript`. A preserved real circuit-component fixture was also uploaded to the exposed board-identification endpoint. It correctly remained **needs_more_evidence** instead of producing an unsupported board conclusion, demonstrating that the confidence gate is retained for non-board imagery.

This temporary service is a preview dependency only. Production deployment remains configured through the separately packaged backend environment template.
