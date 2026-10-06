# FreshSense evaluation data

There are no labeled paired sensor/expiry samples, so the public image data
cannot support Passport fusion metrics. A local, ignored 3,032-image sample
from AgriFreshNET and FruQ-DB has been prepared for an image-only baseline; it
is not included in Git. Details and attribution are in
[`DATASETS.md`](DATASETS.md).

## Recommended public vision dataset

[AgriFreshNET Freshness and Shelf-Life Image Dataset (Mendeley Data)](https://data.mendeley.com/datasets/42m5tb7yv9/1)
is the closest public fit found for bootstrapping the vision classifier. Its
record describes 14,500 RGB images across 24 fruit/vegetable classes with
Fresh, Semi-Fresh, and Rotten labels, and provides both raw and
`Processed_Data.zip` downloads. The processed archive index contains 14,160
images, not the 14,500 stated in the record. It is listed under CC BY 4.0;
retain the attribution and dataset citation if using it. The sampled folders
map Fresh, Semi-Fresh, and Rotten to FreshSense's `fresh`,
`moderately_fresh`, and `spoiled` labels, respectively.

The record does not document stable item/session identifiers or guarantee
that its processed split is duplicate-free. The public-sample script groups
`aug_<n>_` variants by their original filename, then assigns groups to a split;
this filename-based method cannot catch all visual near-duplicates. Do not
randomly split augmented/near-identical frames. The
dataset is produce imagery and contains no matching FreshSense VOC,
temperature, humidity, or package-expiry evidence. It can support a vision
training experiment, but not the Passport fusion comparison or claims about
packaged foods. The record's 14,500 total and average of 569 images per 24
classes do not agree; the processed archive index lists 14,160 image entries.

## Record one sample

Keep each image paired with measurements from the same item and capture time.
Use `schema.csv` as the header. Store image files locally under `data/images/`
and put paths relative to the metadata CSV in `image_path`. Record:

- `freshness_label`: `fresh`, `moderately_fresh`, or `spoiled`, assigned using
  a documented protocol and reviewed by a human. Sensor readings alone and
  appearance alone cannot establish microbial safety.
- `capture_date`: `YYYY-MM-DD`; `expiry_date` in the same format, or blank.
- `split`: `train` or `validation`.
- `group_id`: stable item, batch, or capture-session identifier. Keep each
  group in exactly one split to prevent near-duplicate leakage.
- `gas_value`, `temperature`, and `humidity`: numeric readings, blank when not
  measured. Document sensor model, units, calibration, food type, lighting,
  storage, and handling in `source`/`conditions` or a companion protocol.

For paired collection, follow [`PAIRED_COLLECTION_PROTOCOL.md`](PAIRED_COLLECTION_PROTOCOL.md)
and start from the blank
[`paired_collection_template.csv`](metadata/paired_collection_template.csv).
The expanded template records UTC capture time, per-sensor model and units,
calibration provenance, expiry-date type, and blinded-review provenance. Keep
the completed `paired_collection.csv` local; it is ignored by Git. Validate it
from the repository root before model comparison:

```bash
backend/.venv/bin/python backend/scripts/validate_paired_manifest.py \
  data/metadata/paired_collection.csv
```

Use varied food types, batches, capture sessions, cameras, lighting, and stages.
Choose the split by group before training. A useful evaluation needs enough
independent validation groups in every class; a handful of images is only a
pipeline check and cannot support generalization claims. Do not upload images
of people or private labels. Keep restricted/private data out of version
control.

## Train and compare

Regenerate the deterministic range-extracted sample from the repository root
(network access required):

```bash
backend/.venv/bin/python backend/scripts/prepare_public_dataset_sample.py
```

Then, from `backend/`, with the Python environment active:

```bash
python scripts/train_vision_model.py ../data/metadata/labels.csv
```

Training writes a candidate model and validation metrics. The current
candidate scored 52.6% accuracy and 53.1% macro recall on 445 held-out
AgriFreshNET images (recall: fresh 49.1%, moderately fresh 50.9%, spoiled
59.2%). This is a limited dataset-specific baseline, not evidence of
real-world generalization. The candidate was not promoted to the active model
because the score is too weak to justify activation.

The current public datasets have no paired expiry or sensor fields, so do not
run fusion evaluation on this manifest. With newly collected paired data,
compare the image model with rule-based Passport fusion on held-out groups.
The current candidate can be evaluated without activating it in the app:

```bash
backend/.venv/bin/python backend/scripts/evaluate_fusion.py \
  data/metadata/paired_collection.csv \
  --model-artifact backend/models/vision_model.candidate.json \
  --output data/reports/fusion.json
```

The evaluation reports accuracy, macro precision/recall/F1, class metrics, and
confusion matrices for appearance-only and fused predictions, plus the accuracy
difference. It uses each row's capture date to make expiry assessment
reproducible. Fusion is the existing deterministic rule engine, so this
measures the effect of adding expiry/VOC/environmental inputs; it does not train
a learned multimodal model. Validation groups must be disjoint from training
groups, and each validation row must include paired sensor or expiry evidence.

Do not use `--allow-prototype` for reported model results. That option is only
for checking data and script wiring before a trained artifact exists. Never
describe these model outputs as food safety determinations.

A supplemental raw-image source is documented in
[`DATASETS.md`](DATASETS.md): the expert-labelled Mendeley Fresh and Rotten
Fruits Dataset. It contributes only fresh/spoiled training images. Its labels
must not be used as the moderately-fresh class or in validation because it
lacks group IDs for leakage-safe evaluation.
