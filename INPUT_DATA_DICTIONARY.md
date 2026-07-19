# Input data dictionary

The default input is `data/analysis_input.csv`, with one row per
participant-stage-occasion. The file contains 197 rows: 131 available training
sessions and 66 transfer tests from 22 participants.

| Variable | Type | Description |
| --- | --- | --- |
| `participant_id` | string | Deidentified study code (`S01`-`S22`). |
| `group` | category | `uniform` or `workload_adapted`. |
| `stage` | category | `training` or `transfer`. |
| `occasion` | category | Six training sessions or baseline, immediate (Day 3), and delayed (Day 7) transfer tests. |
| `lt_rn_duration_s` | numeric | Cumulative seconds in the LT-RN coordination state. |
| `lt_rn_count` | numeric | Number of LT-RN events. |
| `rt_ln_duration_s` | numeric | Cumulative seconds in the RT-LN coordination state. |
| `rt_ln_count` | numeric | Number of RT-LN events. |
| `suture_completion_score` | numeric | Transfer-task completion score; full sutures receive 1 point and incomplete attempts may receive 0.25-point increments. Populated only for transfer rows. |
| `mean_active_suture_duration_s` | numeric | Total active suturing time divided by the completion score, in seconds per equivalent suture. Populated only for transfer rows. |

Allowed `occasion` values are:

- Training: `day1_session1`, `day1_session2`, `day2_session1`,
  `day2_session2`, `day3_session1`, `day3_session2`.
- Transfer: `baseline`, `immediate_day3`, `delayed_day7`.

The code requires coordination values for every included row, both transfer
outcomes for every transfer row, and missing transfer-outcome fields for every
training row. No missing transfer outcomes or coordination values are imputed.
