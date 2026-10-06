# FreshSense contribution and evidence plan

## Proposed contribution

FreshSense presents a freshness assessment as a **Freshness Passport**: an
auditable record of the image estimate, optional package expiry date, optional
VOC/environmental readings, the rule-based recommendation, evidence that was
missing, and explicit conflicts between signals. The intended contribution is
the user-facing provenance and conflict handling around a low-cost
multimodal workflow. This is a project hypothesis, not a claim of scientific
priority or demonstrated accuracy; related-work review is needed before making
a novelty claim.

The image classifier is a small interpretable feature model. Cross-modal fusion
currently uses deterministic rules. The work therefore evaluates whether
adding available expiry and sensor evidence changes held-out predictions
relative to the same image model alone. It does not yet implement or claim a
learned multimodal model.

## Evaluation plan

Collect images, human-reviewed freshness labels, capture dates, package expiry
dates, and same-item sensor readings under a documented protocol. Keep items,
batches, or capture sessions grouped wholly in either training or validation.
The schema and operating instructions are in `data/README.md`.

On the untouched validation groups, report accuracy, macro precision, macro
recall, macro F1, per-class recall, and confusion matrices for image-only and
Passport fusion outputs. Include the paired accuracy difference and its 95%
cluster-bootstrap interval by `group_id`. Treat spoiled recall as a key safety
indicator. Report sample and group counts, missing modality rates, sensor
calibration and label protocol, and errors by food type where sample counts
allow. Do not tune decision rules on validation data.

The comparison is meaningful only if labels are independently reviewed,
validation groups are representative and disjoint, and there are enough
independent groups per class. Small convenience samples are pipeline evidence,
not generalization evidence. Expiry and VOC are warning signals; none of these
outputs determine whether food is safe to eat.

## Current evidence status

An image-only candidate was trained on a deterministic 3,032-image sample
from AgriFreshNET and FruQ-DB. It scored 52.6% accuracy and 53.1% macro recall
on 445 held-out AgriFreshNET images; class recalls were 49.1% fresh, 50.9%
moderately fresh, and 59.2% spoiled. The candidate remains inactive because
these sample-specific results are too weak to justify promotion. The sample
uses filename groups for AgriFreshNET, while FruQ-DB is training-only because
its merged archive does not identify source videos. No Passport fusion
comparison was run because neither source contains paired expiry or sensor
evidence. These results establish a working training path, not an accuracy
improvement or a real-world novelty claim; the paired-data study and
related-work review remain open. A paired collection protocol, blank
traceable manifest, pre-evaluation validator, and non-activating candidate
evaluation option are prepared in `data/PAIRED_COLLECTION_PROTOCOL.md`,
`data/metadata/paired_collection_template.csv`, and
`backend/scripts/validate_paired_manifest.py`. No physical paired observations
have been collected yet, so fusion results and any empirical novelty claim
remain open.

The existing image sample was also used for a grouped three-fold hyperparameter
trial and a richer color/spatial feature trial. Neither beat the original
candidate on the fixed validation split (original 52.6% accuracy / 53.1% macro
recall; trials 51.9% / 52.4% and 50.3% / 51.0%). The original candidate remains
the strongest local artifact and all are inactive. Because this split has now
been reused during iteration, these comparisons are exploratory and require a
new independent grouped benchmark for a reliable improvement claim.
