# Data provenance and audit

## Public analysis data

`data/analysis_input.csv` contains one row per participant, analytic stage, and
occasion. It retains only variables required to reproduce the manuscript
analyses and figures.

Removed before release:

- source participant identifiers;
- names and demographic variables;
- video filenames and raw media;
- local or confidential filesystem paths;
- worksheet source-row identifiers;
- unused exploratory variables.

## Completeness

- Participants: 22.
- Transfer-test observations: 66 of 66 planned.
- Training-session observations: 131 of 132 planned.
- Missing values were not imputed.

## Duplicate audit

The analysis worksheet contained a second entry for one workload-adapted
day-3/session-1 key. Comparison with the raw coding sheet showed that the
second raw row was empty. The analysis-ready dataset retains the non-empty row
that matches the raw LT-RN and RT-LN values and excludes the spurious duplicate.

## Restricted source material

Raw video cannot be released publicly because it may contain identifiable
participant information and is subject to consent, ethics, and institutional
restrictions. Requests for governed access should be directed to the
corresponding author and remain subject to institutional approval.

