# Bimanual coordination in laparoscopic suturing

[![Reproduce analyses](https://github.com/ywdreamchaser/bimanual-coordination-laparoscopic-suturing/actions/workflows/reproduce.yml/badge.svg)](https://github.com/ywdreamchaser/bimanual-coordination-laparoscopic-suturing/actions/workflows/reproduce.yml)

Archived release DOI: `10.5281/zenodo.21316250`

Reproducible Python analysis, deidentified processed data, statistical tables,
source data, and publication figures for the study:

> Video-Coded Bimanual Coordination During Laparoscopic Suturing Training Is
> Associated With Post-Training Transfer Performance

## Contents

- `run_analysis.py`: main reproducibility script.
- `src/analysis_utils.py`: validation, statistical analysis, table, and figure helpers.
- `data/analysis_input.csv`: deidentified long-format analysis data.
- `outputs/tables/`: reported model estimates, diagnostics, and table source files.
- `outputs/source_data/`: participant-level and figure source data.
- `outputs/figures/`: four manuscript figures in PNG, TIFF, PDF, and SVG.
- `INPUT_DATA_DICTIONARY.md`: input-variable definitions and allowed values.

Raw videos are not included because they may contain identifiable participant
information and are subject to consent and ethics restrictions.

## Reproduce the results

Python 3.10 or later is recommended.

```bash
python -m pip install -r requirements.txt
python run_analysis.py
```

The verified analysis includes 22 participants, 131 training-session
observations, and all 66 transfer-test observations. P values are two-sided,
nominal, and not adjusted for multiplicity.

## Key outputs

- `outputs/tables/main_effects.csv`: Group, occasion, and Group-by-occasion
  likelihood-ratio tests for all four coordination metrics.
- `outputs/tables/primary_associations.csv`: mutually adjusted associations
  between training-period coordination and transfer performance.
- `outputs/tables/matching_coordination_associations.csv`: corresponding
  training-to-transfer coordination associations.
- `outputs/tables/sensitivity_analysis.csv`: repeated-transfer models with
  participant-clustered standard errors.
- `outputs/tables/predictor_vif.csv`: predictor collinearity diagnostics.

## Data provenance

The public CSV contains study codes (`S01`-`S22`) rather than source participant
identifiers and excludes names, demographics, video filenames, local paths, and
raw media. See `PROVENANCE.md` for the data-audit record.

## Citation

Please cite the archived release rather than the moving `main` branch. Citation
metadata are supplied in `CITATION.cff`. The archived version is identified by
DOI `10.5281/zenodo.21316250`.

## License

The analysis software is released under the MIT License. The processed data and
source-data tables are released under the Creative Commons Attribution 4.0
International License; see `DATA_LICENSE.md`.
