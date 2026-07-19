# Data provenance and audit

## Public analysis data

`data/analysis_input.csv` contains one row per participant, analytic stage,
and occasion. It retains the variables used by the reported statistical
analyses implemented in this repository. Transfer-task outcomes are populated
only for transfer rows in version 1.2.0.

Excluded from the public analysis file:

- source participant identifiers;
- names and demographic variables;
- video filenames and raw media;
- local or confidential filesystem paths;
- worksheet source-row identifiers;
- variables not used by the analyses implemented in this repository.

## Completeness

- Participants: 22.
- Transfer-test observations: 66 of 66 planned.
- Training-session observations: 131 of 132 planned.
- Missing values were not imputed.

## Duplicate-resolution boundary

Duplicate resolution occurred during preparation of the analysis-ready source
worksheet before this public release. The released CSV contains one row for
each participant-stage-occasion key, and the analysis code checks this
constraint. The restricted source workbook and row-level adjudication material
are not included, so the upstream duplicate decision cannot be independently
reconstructed from the public repository alone.

## Version 1.2.0 metadata cleanup

Earlier internal analysis files contained values in transfer-outcome columns
on training rows even though the reported models never read those cells.
Version 1.2.0 clears those training-row cells and validates stage-specific
missingness. Transfer outcomes, coordination measures, row keys, groups, and
all values used by the reported statistical analyses are unchanged.

## Restricted source material

Raw video cannot be released publicly because it may contain identifiable
participant information and is subject to consent, ethics, and institutional
restrictions. Requests for governed access should be directed to the
corresponding author and remain subject to institutional approval.
