# Dataset sources and attribution

The following public datasets are being combined for a produce-image baseline.
Only a deterministic subset was fetched from the archives by HTTP byte ranges;
the subset images and manifest remain under ignored `data/extracted/` and
`data/metadata/labels.csv` and are not committed. The interrupted whole-archive
downloads in `data/downloads/` are partial and were not used for training.

## AgriFreshNET

Dataset: [AgriFreshNET Freshness and Shelf-Life Image Dataset, version 1](https://data.mendeley.com/datasets/42m5tb7yv9/1), Mendeley Data.

The record reports 14,500 RGB images across 24 fruit and vegetable types, with
Fresh, Semi-Fresh, and Rotten stages. The processed archive index contains
14,160 image entries (590 in each of 24 folders), which differs from the
record's stated total. The processed archive used here is
`Processed_Data.zip` (file ID `7b216853-8f3b-47fd-b1ae-df88a367a1d1`), listed
as CC BY 4.0. Cite the dataset record and retain its author attribution when
redistributing derived work. The index count, rather than the record's stated
total, was used for this subset workflow.

## FruQ-DB

Olusola Abayomi-Alli and Robertas Damaševičius. *Fruit Quality Datasets
(FruQ-DB)*, Zenodo, 2022. DOI: [10.5281/zenodo.7224690](https://doi.org/10.5281/zenodo.7224690).

The record reports 5,647 preprocessed 224×224 images from 11 fruit varieties
and three stages: Fresh (2,182), Mild (1,364), and Rotten (2,101). The archive
is listed as CC BY 4.0. Its images are extracted from YouTube time-lapse videos.
The merged archive has no per-video IDs, and the record links ten videos for
eleven varieties (cucumber and strawberry share a URL). The sample therefore
uses FruQ-DB for training only and does not claim video-disjoint validation.

## Combined-use limits

Both sources have image labels only. Neither provides paired FreshSense VOC,
temperature, humidity, or package-expiry observations, so the combination can
train/evaluate the image classifier but cannot substantiate a Passport fusion
comparison. They are produce imagery and may not represent packaged food,
consumer phone cameras, or real storage environments. Preserve each source's
attribution and CC BY 4.0 terms in any redistribution; verify the license
notices included in the archives as well as the record metadata.

## Local training sample

`backend/scripts/prepare_public_dataset_sample.py` deterministically extracts
120 consecutive archive entries from each AgriFreshNET stage/produce folder
and 250 entries from each FruQ-DB stage folder (seed 2026). For AgriFreshNET,
the `aug_<n>_` prefix is removed to group augmented variants by original
filename; one member per group is retained. A stable hash puts about 20% of
AgriFreshNET groups into validation. FruQ-DB is training-only because its
merged archive has no video IDs and the record does not map individual files
to the linked videos. This avoids using unknown related frames for validation,
but does not establish video-level generalization.

The local manifest has 3,032 rows: 2,282 AgriFreshNET and 750 FruQ-DB images;
2,587 train and 445 validation images. This is a convenience sample from
contiguous archive windows, not a random or full-dataset benchmark. Grouping
uses filename conventions, not visual near-duplicate search. Neither dataset
contains paired sensor or expiry readings.

The image classifier was tuned with three-fold group-held-out cross-validation
inside the AgriFreshNET training groups; FruQ-DB was excluded because its
source-video IDs are missing. A hyperparameter-only candidate reached 51.9%
accuracy and 52.4% macro recall on the fixed validation split. An expanded
brightness/color/spatial feature candidate reached 50.3% accuracy and 51.0%
macro recall. Both are below the original candidate (52.6% accuracy, 53.1%
macro recall), which remains the strongest inactive artifact. Since this
validation split has now been reused in model comparisons, all scores here are
exploratory; use a new group-disjoint benchmark before claiming improvement.

## Fresh and Rotten Fruits Dataset (training only)

*Fresh and Rotten Fruits Dataset for Machine-Based Evaluation of Fruit
Quality*, Mendeley Data, DOI [10.17632/bdd69gyhv8.1](https://doi.org/10.17632/bdd69gyhv8.1).
The source describes 3,200 original shop and field images labelled fresh or
rotten with assistance from an agricultural domain expert, under CC BY 4.0.
The Hugging Face conversion
[`Project-AgML/fresh_rotten_fruit_classification`](https://huggingface.co/datasets/Project-AgML/fresh_rotten_fruit_classification)
contains raw Parquet shards as well as a separate augmented collection. Use
only the raw images; augmented rows would increase duplicate leakage and are
not needed for this training-only supplement.

This source has no moderately-fresh class and the conversion does not retain
reliable item or capture-session IDs for a group-disjoint validation split.
Therefore map its fresh/rotten labels to `fresh`/`spoiled` for training only,
assign unique source-qualified group IDs, and never map rotten to
`moderately_fresh` or include these rows in validation. Preserve the original
author attribution and CC BY 4.0 terms when redistributing derived material.
The conversion's dataset card maps class ID `0` to fresh and `1` to rotten;
the Mendeley record remains the citation of record. The raw four-shard import
contains 3,200 images (1,600 per class). Locally these were decoded and
appended as training-only rows in the ignored `data/metadata/labels.csv`
manifest; existing validation rows were not modified. SHA-256 image IDs are
used for source-qualified training groups, since source item/session IDs are
not available.
