# Bimanual coordination analysis

Version 1.2.0 of this package reproduces the reported statistical analyses
implemented in this repository, their derived tables and source-data files,
and four figures for the Surgical Endoscopy manuscript. It uses a
deidentified, analysis-ready CSV and relative paths only.

The package does not regenerate participant demographics or manuscript Table
1, inter-rater reliability statistics, BORIS coding settings, raw video
coding, or results that require restricted source records. Those items are
outside the scope of this public analysis repository.

## Run

The release was tested with Python 3.14.3 and the exact package versions pinned
in `requirements.txt`.

```powershell
python -m pip install -r requirements.txt
python run_analysis.py
```

To use a different location:

```powershell
python run_analysis.py --input data/analysis_input.csv --output outputs
```

To display the release version:

```powershell
python run_analysis.py --version
```

## Analysis sequence

1. Validate required columns, stage-specific labels and missingness,
   participant-group consistency, and unique participant-stage-occasion keys.
2. Average all available training sessions within participant to construct the
   four within-training coordination measures.
3. Average the immediate transfer test on Day 3 and the delayed transfer test
   on Day 7 within participant for the two transfer outcomes and corresponding
   coordination measures.
4. Fit the mutually adjusted participant-level association models, adjusted
   for randomized group, and report unstandardized and standardized
   coefficients, 95% confidence intervals, exact P values, partial R-squared,
   and a Holm check across the eight coordination coefficients in the two
   outcome models.
5. Fit maximum-likelihood random-intercept models and likelihood-ratio tests
   for Group, occasion, and Group by occasion effects at the transfer-test and
   training-session stages.
6. Quantify the relation between the two transfer outcomes and refit focused
   LT-RN models with baseline LT-RN count included.
7. Refit the transfer outcome analysis with both post-training tests retained
   and participant-clustered standard errors as a check of result stability.
8. Refit the participant-level models after adjustment for the corresponding
   baseline transfer outcome and after omitting each participant in turn.
9. Repeat the longitudinal tests after square-root transformation of event
   counts and `log(1+x)` transformation of event durations.
10. For longitudinal terms supported by the omnibus tests, estimate marginal
    means and prespecified raw-scale contrasts. Transfer-test comparisons are
    adjusted within metric, training LT-RN count comparisons are adjusted
    within each stated family, and training LT-RN duration comparisons are
    adjusted against the first session using Holm's method.

P values are two-sided. The eight primary coordination coefficients are also
reported with Holm-adjusted P values as one exploratory measurement family.
Omnibus longitudinal tests are nominal, and targeted follow-up comparison
families use Holm adjustment. Likelihood-ratio chi-square values in the
main-effects table are omnibus test statistics; no separate standardized
effect size was estimated for those multi-degree-of-freedom terms.

## Figure 2 prediction lines

Figure 2 displays observed participant-level points. The line and 95%
confidence band are predictions from the same mutually adjusted model used for
the annotated coefficient: the three non-focal coordination predictors are
held at their sample means and randomized group is held at the observed sample
proportion. The plotted values are exported to
`outputs/source_data/Fig2_adjusted_prediction_lines.csv`.

## Outputs

Some filenames retain the word `sensitivity` for compatibility with earlier
public releases; the manuscript describes these analyses as checks of result
stability.

- `outputs/tables/main_effects.csv`: all four coordination metrics with Group,
  occasion, and interaction tests.
- `outputs/tables/primary_associations.csv`: mutually adjusted transfer
  performance models with nominal and primary-family Holm-adjusted P values.
- `outputs/tables/measurement_correlations.csv`: Pearson correlation between
  the two transfer outcomes.
- `outputs/tables/baseline_coordination_adjusted_full_model.csv`: focused
  models containing training and baseline LT-RN counts and randomized group.
- `outputs/tables/longitudinal_model_information.csv`: observations, variance
  components, and convergence status.
- `outputs/tables/sensitivity_analysis.csv`: repeated-transfer stability check
  with participant-clustered standard errors.
- `outputs/tables/baseline_adjusted_sensitivity.csv`: focal associations after
  adjustment for the corresponding baseline transfer outcome.
- `outputs/tables/leave_one_participant_out_summary.csv`: coefficient and
  P-value ranges after each participant is omitted in turn.
- `outputs/tables/longitudinal_transformation_sensitivity.csv`: transformed-
  outcome longitudinal likelihood-ratio tests.
- `outputs/tables/transfer_estimated_marginal_means.csv` and
  `transfer_pairwise_contrasts_holm.csv`: transfer-test estimated means and all
  three within-metric comparisons.
- `outputs/tables/training_lt_rn_count_*.csv`: group-specific estimated means,
  session simple effects, session-specific group contrasts, and changes from
  the first session for LT-RN count.
- `outputs/tables/training_lt_rn_duration_*.csv`: estimated means and changes
  from the first session for LT-RN duration.
- `outputs/tables/predictor_vif.csv` and `regression_diagnostics.csv`: model
  diagnostics retained for methodological review.
- `outputs/figures/`: each generated figure as PNG, TIFF, PDF, and SVG.
- `outputs/source_data/`: source data for figures and participant-level models.

## Data audit and privacy

The included CSV contains study codes (`S01`-`S22`) rather than source
participant identifiers and excludes file paths, video names, worksheet row
numbers, raw media, demographics, and variables not used by the reported
statistical analyses in this repository. Transfer-outcome fields are populated
only for transfer rows. One planned uniform-difficulty Day 1/session 1 training
observation had no coded coordination values and was not imputed. Thus, 131 of
132 planned training-session observations and all 66 transfer-test
observations are analyzed. See `PROVENANCE.md` for the boundary between public
and restricted source records.

## Public archive

Version 1.2.0 is available at
`https://github.com/ywdreamchaser/bimanual-coordination-laparoscopic-suturing/releases/tag/v1.2.0`
and archived by Zenodo under the version-specific DOI
`10.5281/zenodo.21435999`. Version 1.1.0 remains available as an immutable
historical release at
`https://github.com/ywdreamchaser/bimanual-coordination-laparoscopic-suturing/releases/tag/v1.1.0`
and under Zenodo DOI `10.5281/zenodo.21328522`. The concept DOI
`10.5281/zenodo.21316249` resolves to the latest archived version.
