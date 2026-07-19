# Changelog

## 1.2.0 - 2026-07-18

- Corrected transfer timing to immediate Day 3 and delayed Day 7 throughout
  the public package.
- Updated Figure 2 to use predictions from the mutually adjusted model and
  added its adjusted prediction-line source data.
- Added the current reported supplementary tables, longitudinal follow-up
  estimates, contrasts, and multiplicity checks.
- Cleared transfer-only outcome fields on training rows and enforced the
  stage-specific data contract.
- Narrowed reproducibility claims to the reported statistical analyses
  implemented in this repository.
- Added release-version reporting and regenerated outputs.
- Changed TIFF output to uncompressed RGB at 600 dpi while preserving the
  rendered RGB pixels.

## 1.1.0 - 2026-07-12

- Added models adjusted for the corresponding baseline transfer outcome.
- Added leave-one-participant-out influence analyses.
- Added transformed-outcome sensitivity analyses for the longitudinal models.
- Removed obsolete matching-coordination outputs that are not reported in the manuscript.
- Updated documentation and regenerated all analysis outputs.

## 1.0.0 - 2026-07-11

- Initial public reproducibility release.
- Added deidentified long-format analysis input.
- Added participant-level association models and repeated-transfer sensitivity analysis.
- Added random-intercept likelihood-ratio tests for Group, occasion, and interaction effects.
- Added source-data tables and four publication figures in multiple formats.
- Added model diagnostics, data dictionary, provenance record, and citation metadata.
