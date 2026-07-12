# Bimanual coordination analysis

This package reproduces the numerical results, source-data files, and four
figures reported in the Surgical Endoscopy manuscript. It uses a deidentified,
analysis-ready CSV and relative paths only.

## Run

The archived analysis was tested with Python 3.14.3 and the exact package
versions pinned in `requirements.txt`.

```powershell
python -m pip install -r requirements.txt
python run_analysis.py
```

To use a different location:

```powershell
python run_analysis.py --input data/analysis_input.csv --output outputs
```

## Analysis sequence

1. Validate required columns, labels, participant-group consistency, and unique
   participant-stage-occasion keys.
2. Average all available training sessions within participant to construct the
   four within-training coordination measures.
3. Average immediate and 3-day transfer tests within participant for the two
   transfer performance outcomes and the corresponding coordination measures.
4. Fit the mutually adjusted participant-level association models, adjusted for
   randomized group, and report unstandardized and standardized coefficients,
   95% confidence intervals, exact P values, and partial R-squared.
5. Fit maximum-likelihood random-intercept models and likelihood-ratio tests for
   Group, occasion, and Group by occasion effects at the transfer-test and
   training-session stages.
6. Refit the transfer outcome analysis with both post-training tests retained
   and participant-clustered standard errors as a sensitivity analysis.
7. Refit the participant-level models after adjustment for the corresponding
   baseline transfer outcome and after omitting each participant in turn.
8. Repeat the longitudinal tests after square-root transformation of event
   counts and `log(1+x)` transformation of event durations.

P values are two-sided, nominal, and not adjusted for multiplicity. The
likelihood-ratio χ² values in the main-effects table are omnibus test
statistics; no separate standardized effect size was estimated for those
multi-degree-of-freedom mixed-model terms.

## Outputs

- `outputs/tables/main_effects.csv`: all four coordination metrics with Group,
  occasion, and interaction tests.
- `outputs/tables/primary_associations.csv`: mutually adjusted transfer
  performance models.
- `outputs/tables/longitudinal_model_information.csv`: observations, variance
  components, and convergence status.
- `outputs/tables/sensitivity_analysis.csv`: repeated-transfer sensitivity
  models with participant-clustered standard errors.
- `outputs/tables/baseline_adjusted_sensitivity.csv`: focal associations after
  adjustment for the corresponding baseline transfer outcome.
- `outputs/tables/leave_one_participant_out_summary.csv`: coefficient and
  P-value ranges after each participant is omitted in turn.
- `outputs/tables/longitudinal_transformation_sensitivity.csv`: transformed-
  outcome longitudinal likelihood-ratio tests.
- `outputs/tables/predictor_vif.csv` and `regression_diagnostics.csv`: model
  diagnostics retained for methodological review.
- `outputs/figures/`: each manuscript figure as PNG, TIFF, PDF, and SVG.
- `outputs/source_data/`: source data for figures and participant-level models.

## Data audit and privacy

The included CSV contains study codes (`S01`-`S22`) rather than source
participant identifiers and excludes file paths, video names, worksheet row
numbers, and unused exploratory variables. The source workbook contained a
second entry for one day-3/session-1 training key. Cross-checking against the
raw coding sheet showed that the second raw row was empty; the analysis-ready
record retains the non-empty row that matches the raw coded LT-RN and RT-LN
values. One planned
uniform-difficulty day-1/session-1 training observation had no coded values and
was not imputed. Thus, 131 of 132 planned training-session observations and all
66 transfer-test observations are analyzed.

## Public archive

Version 1.1.0 is available at
`https://github.com/ywdreamchaser/bimanual-coordination-laparoscopic-suturing/releases/tag/v1.1.0`
and is archived as a versioned Zenodo release. Version 1.0.0 remains available
as an immutable historical release.
