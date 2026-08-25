# ElectroCom61 Training Support

Circuit Lens includes the code, a generated data manifest, and a small set of real CC BY test fixtures needed to reproduce the baseline pipeline. The full ElectroCom61 v2 archive is intentionally excluded from the delivery ZIP because it is approximately 137 MB and is already publicly available under CC BY 4.0.[1]

Download the archive from the [ElectroCom61 v2 Mendeley Data record](https://data.mendeley.com/datasets/6scy6h8sjz/2), extract `ElectroCom-61_v2` as `training/data/electrocom61`, and preserve the supplied `data.yaml`, image files, and YOLO label files. The scripts expect the following structure.

```text
training/
  data/
    electrocom61/
      data.yaml
      train/images/     train/labels/
      valid/images/     valid/labels/
      test/images/      test/labels/
```

Run `summarize_electrocom61.py` to regenerate the label summary, then train the TorchScript model with `train_tiny_grid.py`. The package’s measured baseline is intentionally documented as an inspection candidate source rather than a production-accuracy claim; use `evaluate_tiny_grid.py` and improve the model before field deployment.

To retain **all 61 original labels** rather than the initial four-family baseline, use `train_electrocom61_61class.py` and configure the API with the resulting `.pt` model file and `.labels.json` sidecar. Full-class training still needs held-out evaluation and per-class calibration before it can be exposed as anything other than a review-only candidate source.

## References

[1] [ElectroCom61 v2, Mendeley Data, CC BY 4.0.](https://data.mendeley.com/datasets/6scy6h8sjz/2)
