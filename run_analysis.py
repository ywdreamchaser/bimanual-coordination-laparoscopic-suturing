#!/usr/bin/env python
"""Reproduce the reported analyses, derived tables, source data, and figures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.analysis_utils import (
    build_publication_tables,
    compute_diagnostics,
    create_figures,
    load_and_validate_data,
    make_output_dirs,
    make_participant_data,
    run_association_models,
    run_leave_one_participant_out,
    run_longitudinal_followups,
    run_longitudinal_models,
    setup_style,
    summarize_longitudinal,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "data" / "analysis_input.csv"
DEFAULT_OUTPUT = ROOT / "outputs"
ANALYSIS_VERSION = "1.2.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {ANALYSIS_VERSION}",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Deidentified long-format analysis CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Directory for regenerated outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_style()
    dirs = make_output_dirs(args.output.resolve())
    data, completeness = load_and_validate_data(args.input.resolve())
    summary = summarize_longitudinal(data)
    participant, repeated = make_participant_data(data)
    models = run_association_models(participant, repeated)
    longitudinal = run_longitudinal_models(data)
    transformed_longitudinal = run_longitudinal_models(data, transform_skewed=True)
    longitudinal_followups = run_longitudinal_followups(data)
    leave_one_out, leave_one_out_summary = run_leave_one_participant_out(participant)
    build_publication_tables(models, longitudinal, completeness, dirs)
    compute_diagnostics(participant, models, dirs)
    create_figures(participant, models, summary, longitudinal, dirs)

    summary.to_csv(
        dirs.source_data / "longitudinal_group_summary.csv",
        index=False,
        lineterminator="\n",
    )
    participant.to_csv(
        dirs.source_data / "participant_level_analysis_data.csv",
        index=False,
        lineterminator="\n",
    )
    transformed_longitudinal.to_csv(
        dirs.tables / "longitudinal_transformation_sensitivity.csv",
        index=False,
        lineterminator="\n",
    )
    leave_one_out.to_csv(
        dirs.tables / "leave_one_participant_out_detailed.csv",
        index=False,
        lineterminator="\n",
    )
    leave_one_out_summary.to_csv(
        dirs.tables / "leave_one_participant_out_summary.csv",
        index=False,
        lineterminator="\n",
    )
    for name, table in longitudinal_followups.items():
        table.to_csv(
            dirs.tables / f"{name}.csv", index=False, lineterminator="\n"
        )
    run_summary = {
        "analysis_version": ANALYSIS_VERSION,
        "input": args.input.name,
        "rows": len(data),
        "participants": int(data["participant_id"].nunique()),
        "training_rows_available": int((data["stage"] == "training").sum()),
        "transfer_rows_available": int((data["stage"] == "transfer").sum()),
        "output_directory": args.output.name,
    }
    (dirs.root / "run_summary.json").write_text(
        json.dumps(run_summary, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(run_summary, indent=2))


if __name__ == "__main__":
    main()
