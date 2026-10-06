# FreshSense vision model

FreshSense can load a locally trained image classifier from `MODEL_PATH/vision_model.json`. It uses a small multinomial logistic-regression model over interpretable image features, so training and inference need only the existing Pillow dependency. If the artifact is absent, the API uses the explicitly labeled color-and-brightness prototype.

Newly trained artifacts use the v2 feature set (brightness histogram,
saturation, and coarse spatial color features). Inference still accepts the
older eight-feature candidate artifacts.

No dataset or model weights are versioned in this repository. A local
candidate was trained on a 3,032-image sample from AgriFreshNET and FruQ-DB;
its results are described in `../data/DATASETS.md`. Do not describe the active
prototype as a trained model or use either output as a food-safety test. A
photo cannot establish microbial safety, smell, or internal spoilage.

To regenerate the ignored image sample from the public archives, run from the
repository root (network access required):

```bash
backend/.venv/bin/python backend/scripts/prepare_public_dataset_sample.py
```

FruQ-DB is training-only because its merged archive does not retain video IDs.
The current candidate's validation set contains AgriFreshNET groups only.

## Prepare labeled data

Create a CSV with `image_path`, `freshness_label`, `split`, and `group_id`
columns. The same manifest format is used for training and grouped fusion
evaluation; see [../data/README.md](../data/README.md) and
`../data/metadata/schema.csv` for the complete paired-evidence schema.

```csv
image_path,freshness_label,split,group_id,capture_date,expiry_date,gas_value,temperature,humidity
../images/apple_001.jpg,fresh,train,apple_batch_1,2026-01-01,,120,4,55
../images/apple_002.jpg,moderately_fresh,train,apple_batch_2,2026-01-02,2026-01-05,450,8,62
../images/apple_003.jpg,spoiled,train,apple_batch_3,2026-01-03,,850,20,75
../images/apple_101.jpg,fresh,validation,apple_batch_4,2026-02-01,,130,4,53
../images/apple_102.jpg,moderately_fresh,validation,apple_batch_5,2026-02-02,2026-02-05,470,8,65
../images/apple_103.jpg,spoiled,validation,apple_batch_6,2026-02-03,,900,21,78
```

Paths may be absolute or relative to the CSV file. Labels must be `fresh`, `moderately_fresh`, or `spoiled`; `split` must be `train` or `validation`. Keep group IDs disjoint across splits. Include varied food types, lighting, packaging, cameras, and spoilage stages. Have labels reviewed against a documented protocol; appearance alone cannot verify safety. Example dates/readings above are illustrative only and are not data.

## Train and review

From `backend/`:

```bash
python scripts/train_vision_model.py /path/to/freshness.csv
```

The script writes `backend/models/vision_model.candidate.json` by default. It reports validation accuracy, macro and per-class recall, and a confusion matrix; training images stay local. Candidate and active artifacts are ignored by Git. Review the spoiled-class recall and validation examples before activation. The validation metrics describe only the supplied dataset and do not prove real-world safety or generalization.

For deterministic hyperparameter selection, run the grouped cross-validation
tuner from the repository root:

```bash
backend/.venv/bin/python backend/scripts/tune_vision_model.py \
  data/metadata/labels.csv \
  --output backend/models/vision_model.v2.tuned.candidate.json
```

The tuner selects by mean macro recall over three group-held-out folds formed
from AgriFreshNET training groups, then fits the selected configuration on the
full training split and reports the existing validation split once. FruQ-DB is
excluded from cross-validation because its source-video grouping is unknown.

```bash
cp models/vision_model.candidate.json models/vision_model.json
```

Run the promotion command only after reviewing the metrics. The strongest
candidate on the fixed validation split remains the original eight-feature
artifact at 52.6% accuracy and 53.1% macro recall; it has not been promoted.
The grouped hyperparameter trial reached 51.9%/52.4% (accuracy/macro recall),
and the expanded v2 feature trial reached 50.3%/51.0%. Both trials scored lower
on that split and remain inactive. The fixed validation split has now been
reused for model comparisons, so these scores are exploratory, not a fresh
independent benchmark. To use another `MODEL_PATH`, copy a reviewed
candidate to that directory as `vision_model.json`. Restart the API after
promotion. The upload and `/predictions/vision` routes then use the trained
artifact; otherwise they disclose and use the prototype fallback. The
displayed softmax score is marked uncalibrated.

Temperature/humidity/VOC fusion remains rule-based. The Passport names those rules and distinguishes contributing readings from context-only readings.

## Evaluate Passport fusion

Validate a completed paired manifest before comparing vision-only predictions
with Freshness Passport rule fusion:

```bash
python scripts/validate_paired_manifest.py ../data/metadata/paired_collection.csv
python scripts/evaluate_fusion.py ../data/metadata/paired_collection.csv \
  --model-artifact ./models/vision_model.candidate.json \
  --output ../data/reports/fusion.json
```

`--model-artifact` evaluates a candidate file without activating it in the
application. Use `--model-dir` for the active model instead.

The script reports accuracy, macro precision/recall/F1, per-class metrics, and
confusion matrices, including the accuracy difference. It refuses overlapping
train/validation groups and requires paired sensor or expiry evidence in the
validation set. This evaluates the current deterministic fusion rules; it does
not train a multimodal learner. The available public samples have no paired
secondary evidence, so this comparison remains unrun. See
`../data/PAIRED_COLLECTION_PROTOCOL.md` and
`../data/metadata/paired_collection_template.csv` for the collection workflow.
