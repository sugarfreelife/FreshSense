# FreshSense paired-data collection protocol

This protocol prepares paired evidence for an image-only versus Passport-fusion
comparison. It does not define a food-safety test. The current public image
datasets contain no sensor or expiry readings; do not fill gaps with invented
or simulated values.

## Collection design

1. Assign one stable `group_id` to each physical item or traceable batch before
   splitting. Every image, repeated time point, and repeated reading for that
   group must stay in the same split. Assign groups to train or validation
   before examining model predictions; never split individual photos.
2. For an initial study, aim for at least 100 independent groups in each
   freshness class, spread across several food types and storage conditions.
   Treat this as a collection target, not a guarantee of statistical power.
   Revisit sample size after a pilot estimates between-group variation.
3. At each observation, capture the photo and sensor measurements from the
   same item within five minutes. Record one row per image/time point. Repeat
   sensor readings according to the sensor manufacturer's instructions and
   document how repeated measurements were summarized.
4. Photograph the package date when available. Transcribe its printed date
   and whether it is a use-by, best-before, or other date. Leave it blank when
   absent or illegible; do not infer it from purchase or capture dates.
5. Use the project's freshness classes with a written, food-appropriate
   rubric. Have two reviewers label each image without seeing sensor values,
   expiry dates, or model predictions. Record both pseudonymous reviewer IDs
   and an adjudicator when labels disagree. Record the reference method; visual
   labels describe observed appearance and do not certify microbial safety.
6. Record sensor make/model, units, calibration record, capture time, lighting,
   packaging, and storage conditions. Do not compare readings across sensor
   models or units as if they were interchangeable. Preserve raw values and
   apply conversions only in a documented analysis step.
7. Follow institutional and local handling rules. Do not taste study samples;
   isolate and dispose of deteriorated samples safely.

## Manifest fields

Start with `metadata/paired_collection_template.csv`. `capture_time_utc` must
include a UTC offset. `expiry_date` and `expiry_type` are optional. At least one
sensor measurement or package date must be present per row for fusion
evaluation. Leave unmeasured values empty; zero is a real reading. `source` and
`conditions` should describe provenance and handling consistently. Use
`review_status=adjudicated` only after both reviews and any disagreement have
been resolved.

Validate a completed manifest before evaluation:

```bash
backend/.venv/bin/python backend/scripts/validate_paired_manifest.py \
  data/metadata/paired_collection.csv
```

The validator checks row completeness, dates, units and readings, adjudication,
class coverage, paired evidence, and group separation. The fusion evaluator
then produces the image-only versus rule-fusion comparison on validation rows.

## Split and reporting

Use a group-held-out validation split and report group counts as well as image
counts. Report accuracy, macro precision/recall/F1, per-class recall, confusion
matrices, missing-modality rates, and the paired accuracy difference with the
evaluator's group-bootstrap interval. Break results down by food type and
sensor model when group counts permit. Keep the validation split fixed; do not
tune thresholds or collection rules against its results. State the food types,
label rubric, reviewer agreement/adjudication, sensor models and calibration,
units, storage conditions, and any excluded groups with every report.
