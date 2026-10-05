# FreshSense vision model

FreshSense can load a locally trained image classifier from `MODEL_PATH/vision_model.json`. It uses a small multinomial logistic-regression model over interpretable image features, so training and inference need only the existing Pillow dependency. If the artifact is absent, the API uses the explicitly labeled color-and-brightness prototype.

No labeled freshness dataset or trained weights are included in this repository. Do not describe the prototype as a trained model or use either output as a food-safety test. A photo cannot establish microbial safety, smell, or internal spoilage.

## Prepare labeled data

Create a CSV with these columns:

```csv
image_path,label,split
images/apple_001.jpg,fresh,train
images/apple_002.jpg,moderately_fresh,train
images/apple_003.jpg,spoiled,train
images/apple_101.jpg,fresh,validation
images/apple_102.jpg,moderately_fresh,validation
images/apple_103.jpg,spoiled,validation
```

Paths may be absolute or relative to the CSV file. Labels must be `fresh`, `moderately_fresh`, or `spoiled`; `split` must be `train` or `validation`. Keep validation photos separate by item, batch, or capture session from training photos to reduce leakage. Include varied food types, lighting, packaging, cameras, and spoilage stages. Have labels reviewed against a documented protocol; appearance alone cannot verify safety.

## Train and review

From `backend/`:

```bash
python scripts/train_vision_model.py /path/to/freshness.csv
```

The script writes `backend/models/vision_model.candidate.json` by default. It reports validation accuracy, macro and per-class recall, and a confusion matrix; training images stay local. Candidate and active artifacts are ignored by Git. Review the spoiled-class recall and validation examples before activation. The validation metrics describe only the supplied dataset and do not prove real-world safety or generalization.

```bash
cp models/vision_model.candidate.json models/vision_model.json
```

Run the promotion command only after reviewing the metrics. To use another `MODEL_PATH`, copy the reviewed candidate to that directory as `vision_model.json`. Restart the API after promotion. The upload and `/predictions/vision` routes then use the trained artifact; otherwise they disclose and use the prototype fallback. The displayed softmax score is marked uncalibrated.

Temperature/humidity/VOC fusion remains rule-based. The Passport names those rules and distinguishes contributing readings from context-only readings.
