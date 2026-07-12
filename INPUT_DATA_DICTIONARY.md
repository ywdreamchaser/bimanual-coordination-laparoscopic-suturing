# Input data dictionary

The default input is `data/analysis_input.csv`, with one row per
participant-stage-occasion.

| Variable | Type | Description |
| --- | --- | --- |
| `participant_id` | string | Deidentified study code (`S01`-`S22`). |
| `group` | category | `uniform` or `workload_adapted`. |
| `stage` | category | `training` or `transfer`. |
| `occasion` | category | Six training sessions or baseline, immediate, and 3-day transfer tests. |
| `lt_rn_duration_s` | numeric | Cumulative seconds in the LT-RN coordination state. |
| `lt_rn_count` | numeric | Number of LT-RN events. |
| `rt_ln_duration_s` | numeric | Cumulative seconds in the RT-LN coordination state. |
| `rt_ln_count` | numeric | Number of RT-LN events. |
| `suture_completion_score` | numeric | Transfer-task completion score; full sutures receive 1 point and incomplete attempts may receive 0.25-point increments. Missing for training rows. |
| `mean_active_suture_duration_s` | numeric | Total active suturing time divided by the completion score, in seconds per equivalent suture. Missing for training rows. |

Allowed `occasion` values are:

- Training: `day1_session1`, `day1_session2`, `day2_session1`,
  `day2_session2`, `day3_session1`, `day3_session2`.
- Transfer: `baseline`, `immediate`, `day3_followup`.

