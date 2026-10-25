# Preliminary invention disclosure — FreshSense AI

**Working title:** Uncertainty-Triggered Evidence Acquisition for Longitudinal Food-Package Assessment  
**Status:** Internal discussion draft only — not a patent application, legal opinion, or finding of novelty  
**Inventor(s):** To be confirmed with all contributors and the relevant institution  
**Date prepared:** 25 October 2026

## 1. Short summary

FreshSense stores time-stamped package-photo, OCR, user-confirmed date,
product-category, and optional environment observations in a per-scan evidence
record. A rule engine checks for missing or conflicting evidence, selects a
follow-up that can address the highest-priority gap, and links the user to
that capture or review step. Earlier evidence remains in the record with its
source; the follow-up does not silently replace it or convert uncertainty to
a safety verdict.

## 2. Technical field and problem

The concept concerns image-based package assessment and household food
inventory software. A scan can fail to read a date, disagree with another
signal, use illustrative rather than measured environment values, or lack a
product category. Many interfaces show a static result or a generic retry,
leaving the user unsure which observation would help and making it harder to
trace later corrections.

## 3. Proposed technical approach

1. Receive and persist one or more time-stamped observations, including their
   source and modality (for example package image, OCR, manual correction,
   sensor reading, or repeat scan).
2. Calculate explicit evidence states such as present, missing, partial,
   conflicting, or illustrative.
3. Apply a configurable priority policy to select a next acquisition or
   review action appropriate to the evidence state.
4. Present the action with the reason it was selected and route the user to a
   date confirmation, product identification, repeat capture, or sensor review.
5. Append later observations and corrections with provenance so a timeline
   preserves what was originally observed and what was subsequently changed.

Potential embodiments include a mobile camera workflow, package-date OCR,
barcode or product-name lookup, optional calibrated sensors, an item/batch
ledger, and a local-first operation mode. These are concepts for evaluation;
not all are implemented here.

## 4. What this repository currently implements

The prototype has a scan Passport containing evidence, conflicts, limitations,
and a timeline. A deterministic Evidence Recovery Loop prioritizes a conflict,
missing/partial date, unknown category, illustrative sensor values, or a
repeat observation and displays an explanatory follow-up. The next step is
ordinary rule-based application logic. It is not a trained model, validated
freshness predictor, or food-safety determination. The local scan-to-pantry
path supports user review of package dates and batch tracking.

## 5. Possible contribution to investigate

The candidate contribution is the coupling of **evidence provenance,
conflict/gap prioritization, and an explanation-linked next-observation action**
within a longitudinal food-item record. The potentially useful technical
question is whether this closed-loop acquisition policy improves data
completeness or reduces correction effort while maintaining an auditable
observation history. This is a hypothesis, not an established result.

## 6. Preliminary claim sketches (not legal claims)

- A computer-implemented method that identifies a missing or conflicting
  evidence state in a longitudinal packaged-food record, selects a follow-up
  capture or human-review action based on that state, and appends the resulting
  observation with source provenance.
- The method where the user interface presents the selected action together
  with the evidence state that triggered it, and retains prior observations
  after correction or recapture.
- A system and non-transitory computer-readable medium implementing the
  method, with optional package-text and calibrated sensor inputs.

Patent counsel must determine whether any properly limited claim is novel,
inventive/non-obvious, sufficiently disclosed, and eligible subject matter in
the intended jurisdiction. These sketches are prompts for counsel only.

## 7. Prior-art and eligibility risks

This is not an exhaustive prior-art search. Existing publications already
describe food freshness assessment from combinations of images, sensors,
time-series data, package expiry labels, or refrigerator inventory. A broad
claim to “AI freshness from image plus sensors plus expiry date” is therefore
especially risky. The narrower evidence-gap-to-next-observation workflow also
needs a dedicated search for active patent families and non-patent literature.

For India, Section 3(k) excludes a mathematical or business method, a computer
program *per se*, and algorithms. The 2025 Indian Patent Office CRI guidance
discusses examination of computer-related inventions. Whether a particular
implementation meets the applicable technical-effect and other requirements
depends on its claims and full facts; a software label alone is insufficient.
Get advice from a registered patent agent or the institution's IP cell before
filing or public disclosure. Do not describe this draft as a granted patent.

## 8. Evidence and work needed

- Search Indian, WIPO PATENTSCOPE, and other relevant patent databases using
  claim concepts and classifications; review cited families and legal status.
- Ask the university IP cell to establish inventorship, ownership, funding,
  and any disclosure deadlines.
- Implement event-level provenance and correction history consistently, then
  collect usability and error data for the follow-up policy.
- Compare with static-result and generic-retry interfaces. Predefine outcomes
  such as date-confirmation completion, evidence completeness, correction
  rate, time to resolve, and user comprehension.
- Document exact implementation, alternatives, dates, and contributions;
  have counsel draft any application and claims.

## 9. Selected starting references

- [Indian Patents Act, Section 3](https://ipindia.gov.in/acts/patent-act-1970/section-3) — statutory exclusions, including Section 3(k).
- [IP India, Guidelines for Examination of Computer Related Inventions (2025)](https://ipindia.gov.in/frontend/pdf/patents/guidelines/GUIDELINES%20FOR%20EXAMINATION%20OF%20COMPUTER%20RELATED%20INVENTIONS%20(CRIs)%20-%202025.pdf) — official examination guidance.
- [IP India, Filing Process](https://ipindia.gov.in/filing-process) — official filing information.
- [WIPO, Patents](https://www.wipo.int/en/web/patents/protection) — general overview of patent protection and patentability concepts.
- [US20200250531A1, TCS food freshness prediction](https://patents.google.com/patent/US20200250531A1/en) — example of prior art involving time-series visual/sensor freshness data and machine learning.
- [WO2016110749A2, food assessment in a refrigerator](https://patents.google.com/patent/WO2016110749A2/en) — example involving food tracking, expiry-label recognition, and freshness assessment.

These references are initial search leads, not a legal clearance or an
exhaustive novelty opinion.
