#!/usr/bin/env python
"""Reproduce all manuscript statistics, tables, source data, and figures."""

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
    run_longitudinal_models,
    setup_style,
    summarize_longitudinal,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "data" / "analysis_input.csv"
DEFAULT_OUTPUT = ROOT / "outputs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
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
    build_publication_tables(models, longitudinal, completeness, dirs)
    compute_diagnostics(participant, models, dirs)
    create_figures(participant, models, summary, longitudinal, dirs)

    summary.to_csv(dirs.source_data / "longitudinal_group_summary.csv", index=False)
    participant.to_csv(dirs.source_data / "participant_level_analysis_data.csv", index=False)
    run_summary = {
        "input": args.input.name,
        "rows": len(data),
        "participants": int(data["participant_id"].nunique()),
        "training_rows_available": int((data["stage"] == "training").sum()),
        "transfer_rows_available": int((data["stage"] == "transfer").sum()),
        "output_directory": args.output.name,
    }
    (dirs.root / "run_summary.json").write_text(
        json.dumps(run_summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(run_summary, indent=2))


if __name__ == "__main__":
    main()
