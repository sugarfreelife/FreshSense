# FreshSense novelty direction and evidence plan

## Implemented product contribution

FreshSense supports a **Longitudinal Freshness Passport** and a separate
batch-level pantry ledger. A user can name a food item, attach later scans to
that same item, and inspect the chronological record of appearance estimates,
package dates, storage context, warnings, and which modalities contributed to
each scan. Purchase batches keep their own quantity and date provenance;
uncertain OCR dates require user confirmation or correction. Each batch can
record its opened date, storage location, notes, and reminder preference.
Individual scan Passports retain evidence, missing inputs, conflicts, model
identity, and limitations.

Together, the Passport and batch ledger connect repeated observations with
household actions: confirm an unreadable date, track quantity by purchase,
record storage context, and see why a batch is in the reminder queue. The
“use next” cue is an explainable date sort, not a trained recommendation
model. The system does not calculate a validated deterioration rate or claim
a food-safety determination.

## Evidence Recovery Loop (implemented workflow contribution)

For each scan, a deterministic rule selects the highest-priority evidence gap
or conflict and proposes a concrete next step: verify disagreeing signals,
confirm a missing/partial package date, identify an unsupported product,
replace illustrative sensor values, or add a later same-item observation.
The Passport retains the underlying observations and their provenance; the
workflow does not overwrite uncertainty with a model-generated answer. This
is currently ordinary, inspectable application logic, not a learned AI model.

The research hypothesis is that uncertainty-triggered evidence collection
could improve traceability and reduce incomplete household records compared
with showing a static scan result. That hypothesis needs a usability study,
error analysis, and comparison against existing systems before any novelty or
performance claim. See `PATENT_DISCLOSURE_DRAFT.md` for a preliminary
invention-disclosure outline and prior-art risks; it is not a patent filing.

This is an implemented product contribution and a **research hypothesis**, not
a claim of scientific priority or proven accuracy. A related-work review is
still needed before making an academic novelty claim.

## Research question

Does preserving repeated, same-item multimodal observations improve the
traceability and usefulness of freshness assessments compared with isolated
image-only scans? Once enough independently labeled paired observations exist,
does adding package-date and calibrated sensor evidence improve held-out
freshness classification over the image-only baseline?

The second question is not currently answerable from this repository's
available data. Fusion uses deterministic rules; temperature and humidity are
shown as context, and VOC uses an explicitly fixed warning threshold.

## Evaluation plan

Collect repeated images of the same food item across controlled storage time
points, with human-reviewed freshness labels, capture timestamps, food type,
package dates, storage temperature and humidity, and calibrated VOC readings
where available. Keep the item, batch, and capture session grouped wholly in
either training or evaluation to prevent near-duplicate leakage. Follow the
collection protocol and manifest schema under `data/`.

On untouched item groups, compare image-only and Passport-assisted outputs.
Report accuracy, macro precision, macro recall, macro F1, per-class recall,
confusion matrices, missing-modality rates, and paired accuracy difference
with a group-level 95% bootstrap interval. Treat recall for spoiled items as a
key safety indicator. Also report whether the Passport timeline correctly
preserves evidence provenance and highlights conflicting signals. Do not tune
rules on the evaluation groups.

Expiry dates and VOC readings are warning signals. Even a successful study
would not by itself establish food safety or prove that a food is safe to eat.

## Current evidence status

An image-only candidate was trained on a deterministic 3,032-image sample from
AgriFreshNET and FruQ-DB. It scored 52.6% accuracy and 53.1% macro recall on 445
held-out AgriFreshNET images; class recalls were 49.1% fresh, 50.9%
moderately fresh, and 59.2% spoiled. The candidate remains inactive because
these sample-specific results are too weak to justify promotion. No source
data contains paired Passport expiry or sensor evidence, so no fusion
comparison has been run and no empirical multimodal improvement is claimed.

The fixed image split has also been reused during feature and tuning trials;
those comparisons are exploratory. A new independent grouped benchmark and
physical paired observations are required for reliable performance claims.
See `data/PAIRED_COLLECTION_PROTOCOL.md`,
`data/metadata/paired_collection_template.csv`, and
`backend/scripts/validate_paired_manifest.py` for the current collection and
validation workflow. Package label photos use
`data/metadata/package_label_template.csv` and
`backend/scripts/evaluate_package_labels.py` for held-out category and expiry
metrics. No package-label benchmark has been collected yet, so the evaluation
script is ready but no package accuracy claim is available.
