# Version 1.2.0

This release updates the public repository to the analysis package used for
the currently reported statistical results. It corrects transfer-test timing
labels, aligns Figure 2 with the adjusted regression model, and adds the
current derived supplementary-analysis outputs.

## Changes since version 1.1.0

- Corrected transfer occasions throughout the data, code, figures, and
  documentation to baseline, immediate transfer on Day 3, and delayed transfer
  on Day 7.
- Replaced the unadjusted Figure 2 trend lines with predictions from the full
  mutually adjusted model; added the plotted values and confidence limits in
  `outputs/source_data/Fig2_adjusted_prediction_lines.csv`.
- Added Holm-adjusted P values for the eight primary coordination coefficients
  as an exploratory measurement family.
- Added the transfer-outcome correlation and focused models that include
  baseline LT-RN count.
- Added estimated marginal means and prespecified Holm-adjusted follow-up
  contrasts for the reported transfer and training longitudinal effects.
- Retained baseline-outcome-adjusted, repeated-transfer, leave-one-participant-
  out, transformed-outcome, model-information, and diagnostic outputs.
- Cleared transfer-only outcome fields on training rows; this metadata cleanup
  does not alter any analysis input used by the reported models.
- Narrowed repository scope statements to the statistical analyses actually
  implemented here. Participant demographics/Table 1, reliability analyses,
  BORIS settings, raw videos, and restricted source records are not claimed to
  be reproduced.
- Added an explicit `1.2.0` analysis version to the command-line interface and
  run summary.
- Changed TIFF serialization from LZW-compressed RGBA to uncompressed RGB at
  600 dpi (TIFF Compression tag 1). RGB pixels are unchanged, and the PNG
  outputs are unchanged.

## Verified local run

- 22 participants;
- 131 available training-session observations;
- 66 transfer-test observations;
- all 33 generated CSV outputs reproduced byte-for-byte from a clean run;
- all PNG figures reproduced byte-for-byte from version 1.1.0/current source;
- all four new TIFF files are uncompressed RGB at 600 dpi and have RGB pixels
  identical to the prior TIFFs and the corresponding submission TIFFs;
- all 32 longitudinal optimization fits converged.

Raw videos and restricted source records are intentionally excluded.
