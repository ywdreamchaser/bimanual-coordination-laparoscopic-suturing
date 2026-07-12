"""Core analysis and plotting functions for the submission package.

The implementation intentionally uses only NumPy/SciPy for the statistical
models so the reported estimates can be reproduced without a proprietary
statistics package. All analyses operate on the deidentified long-format CSV
described in ``INPUT_DATA_DICTIONARY.md``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize


COORDINATION_VARS = [
    "lt_rn_duration_s",
    "lt_rn_count",
    "rt_ln_duration_s",
    "rt_ln_count",
]
TRANSFER_OUTCOMES = [
    "suture_completion_score",
    "mean_active_suture_duration_s",
]
REQUIRED_COLUMNS = [
    "participant_id",
    "group",
    "stage",
    "occasion",
    *COORDINATION_VARS,
    *TRANSFER_OUTCOMES,
]

TRAINING_OCCASIONS = [
    "day1_session1",
    "day1_session2",
    "day2_session1",
    "day2_session2",
    "day3_session1",
    "day3_session2",
]
TRANSFER_OCCASIONS = ["baseline", "immediate", "day3_followup"]
OCCASION_ORDER = {
    "training": TRAINING_OCCASIONS,
    "transfer": TRANSFER_OCCASIONS,
}
OCCASION_LABELS = {
    "baseline": "Baseline",
    "immediate": "Immediate",
    "day3_followup": "3-day follow-up",
    "day1_session1": "Day 1/S1",
    "day1_session2": "Day 1/S2",
    "day2_session1": "Day 2/S1",
    "day2_session2": "Day 2/S2",
    "day3_session1": "Day 3/S1",
    "day3_session2": "Day 3/S2",
}
GROUP_LABELS = {
    "uniform": "Uniform difficulty",
    "workload_adapted": "Workload-adapted",
}
GROUP_COLORS = {"uniform": "#3F6F8F", "workload_adapted": "#C96F3D"}
METRIC_LABELS = {
    "lt_rn_duration_s": "LT-RN total duration (s)",
    "lt_rn_count": "LT-RN occurrences",
    "rt_ln_duration_s": "RT-LN total duration (s)",
    "rt_ln_count": "RT-LN occurrences",
}
SHORT_LABELS = {
    "lt_rn_duration_s": "LT-RN duration",
    "lt_rn_count": "LT-RN count",
    "rt_ln_duration_s": "RT-LN duration",
    "rt_ln_count": "RT-LN count",
}
OUTCOME_LABELS = {
    "suture_completion_score": "Transfer suture-completion score",
    "mean_active_suture_duration_s": "Transfer mean active suture duration",
}

NEUTRAL = "#2D3436"
GRID = "#D9DEE2"


@dataclass(frozen=True)
class OutputDirs:
    root: Path
    tables: Path
    figures: Path
    source_data: Path


def make_output_dirs(root: Path) -> OutputDirs:
    dirs = OutputDirs(
        root=root,
        tables=root / "tables",
        figures=root / "figures",
        source_data=root / "source_data",
    )
    for path in (dirs.root, dirs.tables, dirs.figures, dirs.source_data):
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def setup_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 7,
            "axes.titlesize": 8.5,
            "axes.labelsize": 7,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "legend.fontsize": 6.5,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.55,
            "ytick.major.width": 0.55,
            "xtick.major.size": 2.5,
            "ytick.major.size": 2.5,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.dpi": 600,
            "axes.unicode_minus": False,
        }
    )


def clean_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#60666B")
    ax.spines["bottom"].set_color("#60666B")
    ax.tick_params(colors="#343A40")
    ax.grid(axis="y", color=GRID, linewidth=0.45, alpha=0.85)
    ax.set_axisbelow(True)


def add_panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.13,
        1.06,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        fontweight="bold",
        color=NEUTRAL,
    )


def save_figure(fig: plt.Figure, base: Path) -> None:
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".png"), dpi=300, bbox_inches="tight")
    try:
        fig.savefig(
            base.with_suffix(".tiff"),
            dpi=600,
            bbox_inches="tight",
            pil_kwargs={"compression": "tiff_lzw"},
        )
    except TypeError:
        fig.savefig(base.with_suffix(".tiff"), dpi=600, bbox_inches="tight")


def p_text(value: float) -> str:
    if not np.isfinite(value):
        return "NA"
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}".replace("0.", ".")


def ci_text(low: float, high: float, decimals: int = 3) -> str:
    return f"{low:.{decimals}f} to {high:.{decimals}f}"


def load_and_validate_data(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not path.exists():
        raise FileNotFoundError(f"Input data not found: {path}")
    data = pd.read_csv(path, na_values=["", "NA", "NaN"])
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing_columns:
        raise ValueError(f"Input is missing required columns: {missing_columns}")

    data = data[REQUIRED_COLUMNS].copy()
    for column in ("participant_id", "group", "stage", "occasion"):
        data[column] = data[column].astype(str).str.strip()
    for column in COORDINATION_VARS + TRANSFER_OUTCOMES:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    allowed_groups = set(GROUP_LABELS)
    allowed_stages = set(OCCASION_ORDER)
    if not set(data["group"]).issubset(allowed_groups):
        raise ValueError(f"Unexpected group labels: {sorted(set(data['group']) - allowed_groups)}")
    if not set(data["stage"]).issubset(allowed_stages):
        raise ValueError(f"Unexpected stage labels: {sorted(set(data['stage']) - allowed_stages)}")
    for stage, occasions in OCCASION_ORDER.items():
        observed = set(data.loc[data["stage"] == stage, "occasion"])
        if not observed.issubset(set(occasions)):
            raise ValueError(f"Unexpected {stage} occasion labels: {sorted(observed - set(occasions))}")

    key = ["participant_id", "stage", "occasion"]
    duplicates = data[data.duplicated(key, keep=False)]
    if not duplicates.empty:
        raise ValueError(
            "Each participant-stage-occasion must be unique. Duplicate keys: "
            + duplicates[key].drop_duplicates().to_dict(orient="records").__repr__()
        )
    group_counts = data.groupby("participant_id")["group"].nunique()
    if (group_counts != 1).any():
        raise ValueError("Each participant must belong to exactly one group.")
    if data[COORDINATION_VARS].isna().any().any():
        missing = data.loc[data[COORDINATION_VARS].isna().any(axis=1), key]
        raise ValueError(f"Coordination values are missing in rows: {missing.to_dict(orient='records')}")

    transfer = data[data["stage"] == "transfer"]
    if transfer[TRANSFER_OUTCOMES].isna().any().any():
        raise ValueError("Transfer rows must contain both transfer outcome values.")

    participant_groups = data[["participant_id", "group"]].drop_duplicates()
    expected_rows = []
    for row in participant_groups.itertuples(index=False):
        for stage, occasions in OCCASION_ORDER.items():
            for occasion in occasions:
                expected_rows.append(
                    {
                        "participant_id": row.participant_id,
                        "group": row.group,
                        "stage": stage,
                        "occasion": occasion,
                    }
                )
    expected = pd.DataFrame(expected_rows)
    completeness = expected.merge(
        data[key].assign(available=1),
        on=key,
        how="left",
    )
    completeness["available"] = completeness["available"].fillna(0).astype(int)

    sort_stage = pd.Categorical(data["stage"], categories=["transfer", "training"], ordered=True)
    data = data.assign(_stage_order=sort_stage)
    data = data.sort_values(["_stage_order", "participant_id", "occasion"]).drop(columns="_stage_order")
    return data.reset_index(drop=True), completeness


def mean_ci(values: pd.Series) -> tuple[float, float, float, float, float, int]:
    arr = pd.to_numeric(values, errors="coerce").dropna().to_numpy(float)
    n = len(arr)
    if n == 0:
        return np.nan, np.nan, np.nan, np.nan, np.nan, 0
    mean = float(np.mean(arr))
    sd = float(np.std(arr, ddof=1)) if n > 1 else np.nan
    se = sd / math.sqrt(n) if n > 1 else np.nan
    critical = stats.t.ppf(0.975, n - 1) if n > 1 else np.nan
    return mean, sd, se, mean - critical * se, mean + critical * se, n


def summarize_longitudinal(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (stage, occasion, group), subset in data.groupby(
        ["stage", "occasion", "group"], sort=False
    ):
        for metric in COORDINATION_VARS:
            mean, sd, se, low, high, n = mean_ci(subset[metric])
            rows.append(
                {
                    "stage": stage,
                    "occasion": occasion,
                    "occasion_label": OCCASION_LABELS[occasion],
                    "group": group,
                    "group_label": GROUP_LABELS[group],
                    "metric": metric,
                    "metric_label": METRIC_LABELS[metric],
                    "n": n,
                    "mean": mean,
                    "sd": sd,
                    "se": se,
                    "ci95_low": low,
                    "ci95_high": high,
                }
            )
    return pd.DataFrame(rows)


def make_participant_data(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    training = data[data["stage"] == "training"]
    training_mean = (
        training.groupby(["participant_id", "group"], as_index=False)[COORDINATION_VARS]
        .mean()
        .rename(columns={column: f"training_mean_{column}" for column in COORDINATION_VARS})
    )
    post_transfer = data[
        (data["stage"] == "transfer") & (data["occasion"].isin(["immediate", "day3_followup"]))
    ]
    repeated = post_transfer.merge(training_mean, on=["participant_id", "group"], how="left")
    post_mean = (
        post_transfer.groupby(["participant_id", "group"], as_index=False)[
            COORDINATION_VARS + TRANSFER_OUTCOMES
        ]
        .mean()
        .rename(columns={column: f"post_transfer_mean_{column}" for column in COORDINATION_VARS + TRANSFER_OUTCOMES})
    )
    participant = post_mean.merge(training_mean, on=["participant_id", "group"], how="left")
    baseline = (
        data[(data["stage"] == "transfer") & (data["occasion"] == "baseline")][
            ["participant_id", "group", *TRANSFER_OUTCOMES]
        ]
        .rename(columns={column: f"baseline_{column}" for column in TRANSFER_OUTCOMES})
    )
    participant = participant.merge(
        baseline, on=["participant_id", "group"], how="left", validate="one_to_one"
    )
    return participant, repeated


def design_matrix(
    frame: pd.DataFrame,
    predictors: list[str],
    include_group: bool = True,
    standardize: bool = False,
) -> tuple[np.ndarray, list[str]]:
    columns = [np.ones(len(frame), dtype=float)]
    names = ["Intercept"]
    for predictor in predictors:
        values = pd.to_numeric(frame[predictor], errors="coerce").to_numpy(float)
        if standardize:
            sd = np.nanstd(values, ddof=1)
            values = (values - np.nanmean(values)) / sd if sd > 0 else values * np.nan
        columns.append(values)
        names.append(predictor)
    if include_group:
        columns.append((frame["group"] == "workload_adapted").astype(float).to_numpy())
        names.append("group_workload_adapted")
    return np.column_stack(columns), names


def fit_ols(
    frame: pd.DataFrame,
    outcome: str,
    predictors: list[str],
    outcome_label: str,
    standardize: bool = False,
    cluster: str | None = None,
) -> pd.DataFrame:
    matrix, names = design_matrix(frame, predictors, include_group=True, standardize=standardize)
    response = pd.to_numeric(frame[outcome], errors="coerce").to_numpy(float)
    if standardize:
        response_sd = np.nanstd(response, ddof=1)
        response = (response - np.nanmean(response)) / response_sd
    mask = np.isfinite(response) & np.all(np.isfinite(matrix), axis=1)
    matrix = matrix[mask]
    response = response[mask]
    work = frame.loc[mask].copy()

    n, k = matrix.shape
    beta = np.linalg.lstsq(matrix, response, rcond=None)[0]
    residuals = response - matrix @ beta
    df_resid = n - k
    xtx_inverse = np.linalg.pinv(matrix.T @ matrix)

    if cluster is None:
        covariance = (residuals @ residuals / df_resid) * xtx_inverse
        df_for_p = df_resid
        se_type = "classical"
    else:
        clusters = work[cluster].astype(str).to_numpy()
        meat = np.zeros((k, k), dtype=float)
        unique_clusters = np.unique(clusters)
        for cluster_value in unique_clusters:
            index = clusters == cluster_value
            x_group = matrix[index]
            u_group = residuals[index][:, None]
            meat += x_group.T @ (u_group @ u_group.T) @ x_group
        covariance = xtx_inverse @ meat @ xtx_inverse
        g = len(unique_clusters)
        covariance *= (g / (g - 1)) * ((n - 1) / (n - k))
        df_for_p = g - 1
        se_type = "participant-clustered"

    standard_errors = np.sqrt(np.maximum(np.diag(covariance), 0))
    t_values = beta / standard_errors
    p_values = 2 * stats.t.sf(np.abs(t_values), df_for_p)
    critical = stats.t.ppf(0.975, df_for_p)
    total_ss = float(np.sum((response - np.mean(response)) ** 2))
    residual_ss = float(np.sum(residuals**2))
    r_squared = 1 - residual_ss / total_ss
    adjusted_r_squared = 1 - (1 - r_squared) * (n - 1) / df_resid

    rows = []
    for name, estimate, std_error, t_value, p_value in zip(
        names, beta, standard_errors, t_values, p_values
    ):
        partial_r2 = t_value**2 / (t_value**2 + df_for_p)
        rows.append(
            {
                "model_outcome": outcome_label,
                "outcome_variable": outcome,
                "term": name,
                "estimate": estimate,
                "std_error": std_error,
                "ci95_low": estimate - critical * std_error,
                "ci95_high": estimate + critical * std_error,
                "t": t_value,
                "df": df_for_p,
                "p_value": p_value,
                "partial_r2": partial_r2,
                "n": n,
                "model_df_resid": df_resid,
                "r2": r_squared,
                "adjusted_r2": adjusted_r_squared,
                "standardized": standardize,
                "se_type": se_type,
            }
        )
    return pd.DataFrame(rows)


def run_association_models(
    participant: pd.DataFrame,
    repeated: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    predictors = [f"training_mean_{metric}" for metric in COORDINATION_VARS]
    primary = []
    standardized = []
    for outcome in TRANSFER_OUTCOMES:
        outcome_column = f"post_transfer_mean_{outcome}"
        primary.append(
            fit_ols(participant, outcome_column, predictors, OUTCOME_LABELS[outcome])
        )
        standardized.append(
            fit_ols(
                participant,
                outcome_column,
                predictors,
                OUTCOME_LABELS[outcome],
                standardize=True,
            )
        )

    sensitivity = []
    for outcome in TRANSFER_OUTCOMES:
        sensitivity.append(
            fit_ols(
                repeated,
                outcome,
                predictors,
                OUTCOME_LABELS[outcome],
                cluster="participant_id",
            )
        )

    baseline_adjusted = []
    for outcome in TRANSFER_OUTCOMES:
        baseline_adjusted.append(
            fit_ols(
                participant,
                f"post_transfer_mean_{outcome}",
                [*predictors, f"baseline_{outcome}"],
                OUTCOME_LABELS[outcome],
            )
        )
    return {
        "primary": pd.concat(primary, ignore_index=True),
        "standardized": pd.concat(standardized, ignore_index=True),
        "sensitivity": pd.concat(sensitivity, ignore_index=True),
        "baseline_adjusted": pd.concat(baseline_adjusted, ignore_index=True),
    }


def run_leave_one_participant_out(participant: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Refit the primary models after omitting each participant in turn."""
    predictors = [f"training_mean_{metric}" for metric in COORDINATION_VARS]
    detailed_rows = []
    for outcome in TRANSFER_OUTCOMES:
        outcome_label = OUTCOME_LABELS[outcome]
        for participant_id in participant["participant_id"].astype(str):
            reduced = participant[participant["participant_id"].astype(str) != participant_id]
            fitted = fit_ols(
                reduced,
                f"post_transfer_mean_{outcome}",
                predictors,
                outcome_label,
            )
            focal = fitted[fitted["term"] == "training_mean_lt_rn_count"].iloc[0]
            detailed_rows.append(
                {
                    "model_outcome": outcome_label,
                    "omitted_participant": participant_id,
                    "estimate": focal["estimate"],
                    "ci95_low": focal["ci95_low"],
                    "ci95_high": focal["ci95_high"],
                    "p_value": focal["p_value"],
                    "n": focal["n"],
                }
            )

    detailed = pd.DataFrame(detailed_rows)
    summary_rows = []
    for outcome_label, subset in detailed.groupby("model_outcome", sort=False):
        summary_rows.append(
            {
                "model_outcome": outcome_label,
                "estimate_min": subset["estimate"].min(),
                "estimate_max": subset["estimate"].max(),
                "p_value_min": subset["p_value"].min(),
                "p_value_max": subset["p_value"].max(),
                "omissions_with_p_below_0_05": int((subset["p_value"] < 0.05).sum()),
                "total_omissions": len(subset),
            }
        )
    return detailed, pd.DataFrame(summary_rows)


def build_longitudinal_design(
    frame: pd.DataFrame,
    stage: str,
    include_group: bool,
    include_occasion: bool,
    include_interaction: bool,
) -> np.ndarray:
    work = frame.copy()
    work["occasion"] = pd.Categorical(
        work["occasion"], categories=OCCASION_ORDER[stage], ordered=True
    )
    group = (work["group"] == "workload_adapted").astype(float).to_numpy()
    columns = [np.ones(len(work), dtype=float)]
    if include_group:
        columns.append(group)
    dummies = pd.get_dummies(work["occasion"], drop_first=True, dtype=float)
    if include_occasion:
        columns.extend(dummies[column].to_numpy(float) for column in dummies.columns)
    if include_interaction:
        columns.extend(group * dummies[column].to_numpy(float) for column in dummies.columns)
    return np.column_stack(columns)


def _vinv_dot(matrix: np.ndarray, residual_variance: float, random_variance: float) -> np.ndarray:
    n = matrix.shape[0]
    a = 1.0 / residual_variance
    b = random_variance / (
        residual_variance * (residual_variance + n * random_variance)
    )
    return a * matrix - b * np.ones((n, 1)) @ np.sum(matrix, axis=0, keepdims=True)


def fit_random_intercept_ml(
    response: np.ndarray,
    design: np.ndarray,
    groups: np.ndarray,
) -> dict[str, float | int | bool | np.ndarray]:
    mask = np.isfinite(response) & np.all(np.isfinite(design), axis=1)
    response = response[mask].astype(float)
    design = design[mask].astype(float)
    groups = groups[mask].astype(str)
    n, k = design.shape
    group_indices = [np.where(groups == level)[0] for level in np.unique(groups)]
    response_variance = max(float(np.var(response, ddof=1)), 1e-6)

    def beta_and_loglik(log_variances: np.ndarray) -> tuple[np.ndarray, float, np.ndarray]:
        residual_variance = float(np.exp(log_variances[0]))
        random_variance = float(np.exp(log_variances[1]))
        xt_vinv_x = np.zeros((k, k), dtype=float)
        xt_vinv_y = np.zeros(k, dtype=float)
        log_determinant = 0.0
        for index in group_indices:
            x_group = design[index]
            y_group = response[index]
            vinv_x = _vinv_dot(x_group, residual_variance, random_variance)
            vinv_y = _vinv_dot(
                y_group[:, None], residual_variance, random_variance
            ).ravel()
            xt_vinv_x += x_group.T @ vinv_x
            xt_vinv_y += x_group.T @ vinv_y
            group_n = len(index)
            log_determinant += (group_n - 1) * math.log(residual_variance) + math.log(
                residual_variance + group_n * random_variance
            )
        covariance_beta = np.linalg.pinv(xt_vinv_x)
        beta = covariance_beta @ xt_vinv_y
        quadratic = 0.0
        for index in group_indices:
            residual = response[index] - design[index] @ beta
            vinv_residual = _vinv_dot(
                residual[:, None], residual_variance, random_variance
            ).ravel()
            quadratic += float(residual @ vinv_residual)
        log_likelihood = -0.5 * (
            n * math.log(2 * math.pi) + log_determinant + quadratic
        )
        return beta, log_likelihood, covariance_beta

    def objective(log_variances: np.ndarray) -> float:
        return -beta_and_loglik(log_variances)[1]

    initial = np.log(
        [max(response_variance * 0.65, 1e-6), max(response_variance * 0.25, 1e-6)]
    )
    bounds = [
        (math.log(response_variance * 1e-8), math.log(response_variance * 1e4)),
        (math.log(response_variance * 1e-8), math.log(response_variance * 1e4)),
    ]
    optimization = minimize(objective, initial, method="L-BFGS-B", bounds=bounds)
    beta, log_likelihood, covariance_beta = beta_and_loglik(optimization.x)
    return {
        "beta": beta,
        "se": np.sqrt(np.maximum(np.diag(covariance_beta), 0)),
        "loglik": log_likelihood,
        "rank": int(np.linalg.matrix_rank(design)),
        "n": n,
        "n_participants": len(group_indices),
        "residual_variance": float(np.exp(optimization.x[0])),
        "random_intercept_variance": float(np.exp(optimization.x[1])),
        "converged": bool(optimization.success),
    }


def run_longitudinal_models(
    data: pd.DataFrame, transform_skewed: bool = False
) -> pd.DataFrame:
    rows = []
    for stage in ("training", "transfer"):
        subset = data[data["stage"] == stage].copy()
        participant_ids = subset["participant_id"].to_numpy(str)
        for metric in COORDINATION_VARS:
            response = subset[metric].to_numpy(float)
            transformation = "none"
            if transform_skewed:
                if metric.endswith("_count"):
                    response = np.sqrt(np.clip(response, 0, None))
                    transformation = "square_root"
                else:
                    response = np.log1p(np.clip(response, 0, None))
                    transformation = "log1p"
            designs = {
                "group_only": build_longitudinal_design(subset, stage, True, False, False),
                "occasion_only": build_longitudinal_design(subset, stage, False, True, False),
                "main": build_longitudinal_design(subset, stage, True, True, False),
                "full": build_longitudinal_design(subset, stage, True, True, True),
            }
            fits = {
                name: fit_random_intercept_ml(response, design, participant_ids)
                for name, design in designs.items()
            }
            tests = [
                ("Group", "occasion_only", "main"),
                ("Occasion", "group_only", "main"),
                ("Group x occasion", "main", "full"),
            ]
            for term, reduced_name, full_name in tests:
                reduced = fits[reduced_name]
                full = fits[full_name]
                df_difference = int(full["rank"]) - int(reduced["rank"])
                chi_square = max(
                    0.0, 2 * (float(full["loglik"]) - float(reduced["loglik"]))
                )
                rows.append(
                    {
                        "stage": stage,
                        "metric": metric,
                        "metric_label": METRIC_LABELS[metric],
                        "term": term,
                        "transformation": transformation,
                        "chi_square": chi_square,
                        "df": df_difference,
                        "p_value": stats.chi2.sf(chi_square, df_difference),
                        "n_observations": int(full["n"]),
                        "n_participants": int(full["n_participants"]),
                        "random_intercept_variance": float(
                            full["random_intercept_variance"]
                        ),
                        "residual_variance": float(full["residual_variance"]),
                        "converged": bool(full["converged"]),
                    }
                )
    return pd.DataFrame(rows)


def term_row(table: pd.DataFrame, outcome: str, term: str) -> pd.Series:
    match = table[(table["model_outcome"] == outcome) & (table["term"] == term)]
    if match.empty:
        raise ValueError(f"Missing model term {term!r} for {outcome!r}")
    return match.iloc[0]


def longitudinal_row(table: pd.DataFrame, stage: str, metric: str, term: str) -> pd.Series:
    match = table[
        (table["stage"] == stage)
        & (table["metric"] == metric)
        & (table["term"] == term)
    ]
    if match.empty:
        raise ValueError(f"Missing longitudinal result: {stage}, {metric}, {term}")
    return match.iloc[0]


def build_publication_tables(
    models: dict[str, pd.DataFrame],
    longitudinal: pd.DataFrame,
    completeness: pd.DataFrame,
    dirs: OutputDirs,
) -> dict[str, pd.DataFrame]:
    stage_labels = {"transfer": "Transfer tests", "training": "Training sessions"}
    main_effect_rows = []
    for stage in ("transfer", "training"):
        for metric in COORDINATION_VARS:
            group = longitudinal_row(longitudinal, stage, metric, "Group")
            occasion = longitudinal_row(longitudinal, stage, metric, "Occasion")
            interaction = longitudinal_row(
                longitudinal, stage, metric, "Group x occasion"
            )
            main_effect_rows.append(
                {
                    "Stage": stage_labels[stage],
                    "Metric": METRIC_LABELS[metric],
                    "Group, χ² (df)": f"{group['chi_square']:.2f} ({int(group['df'])})",
                    "Group p value": p_text(float(group["p_value"])),
                    "Occasion, χ² (df)": f"{occasion['chi_square']:.2f} ({int(occasion['df'])})",
                    "Occasion p value": p_text(float(occasion["p_value"])),
                    "Group × occasion, χ² (df)": (
                        f"{interaction['chi_square']:.2f} ({int(interaction['df'])})"
                    ),
                    "Interaction p value": p_text(float(interaction["p_value"])),
                }
            )
    main_effects = pd.DataFrame(main_effect_rows)

    predictor_labels = {
        f"training_mean_{metric}": f"Within-training mean {SHORT_LABELS[metric]}"
        + (" (s)" if "duration" in metric else "")
        for metric in COORDINATION_VARS
    }
    predictor_labels["group_workload_adapted"] = (
        "Workload-adapted group (vs uniform difficulty)"
    )
    primary_rows = []
    for outcome in OUTCOME_LABELS.values():
        for term in [
            *(f"training_mean_{metric}" for metric in COORDINATION_VARS),
            "group_workload_adapted",
        ]:
            row = term_row(models["primary"], outcome, term)
            primary_rows.append(
                {
                    "Outcome": outcome,
                    "Predictor": predictor_labels[term],
                    "B": f"{row['estimate']:.3f}",
                    "95% CI": ci_text(row["ci95_low"], row["ci95_high"]),
                    "p value": p_text(row["p_value"]),
                    "Partial R2": f"{row['partial_r2']:.3f}",
                }
            )
    primary_table = pd.DataFrame(primary_rows)

    model_info_rows = []
    for stage in ("transfer", "training"):
        for metric in COORDINATION_VARS:
            row = longitudinal_row(longitudinal, stage, metric, "Group x occasion")
            model_info_rows.append(
                {
                    "Stage": stage_labels[stage],
                    "Metric": METRIC_LABELS[metric],
                    "Observations": str(int(row["n_observations"])),
                    "Participants": str(int(row["n_participants"])),
                    "Random-intercept variance": f"{row['random_intercept_variance']:.3f}",
                    "Residual variance": f"{row['residual_variance']:.3f}",
                    "Converged": "Yes" if row["converged"] else "No",
                }
            )
    model_information = pd.DataFrame(model_info_rows)

    sensitivity_rows = []
    for outcome in OUTCOME_LABELS.values():
        row = term_row(
            models["sensitivity"], outcome, "training_mean_lt_rn_count"
        )
        sensitivity_rows.append(
            {
                "Outcome": outcome,
                "Predictor": "Within-training mean LT-RN count",
                "B": f"{row['estimate']:.3f}",
                "95% CI": ci_text(row["ci95_low"], row["ci95_high"]),
                "p value": p_text(row["p_value"]),
            }
        )
    sensitivity_table = pd.DataFrame(sensitivity_rows)

    baseline_adjusted_rows = []
    for outcome in OUTCOME_LABELS.values():
        row = term_row(
            models["baseline_adjusted"], outcome, "training_mean_lt_rn_count"
        )
        baseline_adjusted_rows.append(
            {
                "Outcome": outcome,
                "Predictor": "Within-training mean LT-RN count",
                "B": f"{row['estimate']:.3f}",
                "95% CI": ci_text(row["ci95_low"], row["ci95_high"]),
                "p value": p_text(row["p_value"]),
            }
        )
    baseline_adjusted_table = pd.DataFrame(baseline_adjusted_rows)

    completeness_summary = (
        completeness.groupby(["stage", "group"], as_index=False)
        .agg(available=("available", "sum"), expected=("available", "size"))
    )
    tables = {
        "main_effects": main_effects,
        "primary_associations": primary_table,
        "longitudinal_model_information": model_information,
        "sensitivity_analysis": sensitivity_table,
        "baseline_adjusted_sensitivity": baseline_adjusted_table,
        "data_completeness": completeness_summary,
    }
    for name, table in tables.items():
        table.to_csv(dirs.tables / f"{name}.csv", index=False)
    models["primary"].to_csv(dirs.tables / "primary_associations_full_model.csv", index=False)
    models["standardized"].to_csv(
        dirs.tables / "primary_associations_standardized.csv", index=False
    )
    models["sensitivity"].to_csv(
        dirs.tables / "sensitivity_analysis_full_model.csv", index=False
    )
    models["baseline_adjusted"].to_csv(
        dirs.tables / "baseline_adjusted_sensitivity_full_model.csv", index=False
    )
    longitudinal.to_csv(dirs.tables / "longitudinal_likelihood_ratio_tests.csv", index=False)
    return tables


def compute_diagnostics(
    participant: pd.DataFrame,
    models: dict[str, pd.DataFrame],
    dirs: OutputDirs,
) -> None:
    predictors = [f"training_mean_{metric}" for metric in COORDINATION_VARS]
    vif_rows = []
    for predictor in predictors:
        response = participant[predictor].to_numpy(float)
        other_predictors = [column for column in predictors if column != predictor]
        design = np.column_stack(
            [np.ones(len(participant)), participant[other_predictors].to_numpy(float)]
        )
        estimate = np.linalg.lstsq(design, response, rcond=None)[0]
        residual = response - design @ estimate
        r_squared = 1 - float(residual @ residual) / float(
            np.sum((response - response.mean()) ** 2)
        )
        vif_rows.append(
            {"predictor": predictor, "r2_from_other_predictors": r_squared, "vif": 1 / (1 - r_squared)}
        )
    pd.DataFrame(vif_rows).to_csv(dirs.tables / "predictor_vif.csv", index=False)

    diagnostic_rows = []
    for outcome in TRANSFER_OUTCOMES:
        outcome_label = OUTCOME_LABELS[outcome]
        outcome_column = f"post_transfer_mean_{outcome}"
        design, _ = design_matrix(participant, predictors, include_group=True)
        response = participant[outcome_column].to_numpy(float)
        beta = np.linalg.lstsq(design, response, rcond=None)[0]
        residuals = response - design @ beta
        shapiro = stats.shapiro(residuals)
        diagnostic_rows.append(
            {
                "model_outcome": outcome_label,
                "shapiro_w": shapiro.statistic,
                "shapiro_p": shapiro.pvalue,
                "maximum_absolute_standardized_residual": np.max(
                    np.abs((residuals - residuals.mean()) / residuals.std(ddof=1))
                ),
                "n": len(response),
                "number_of_model_predictors_excluding_intercept": design.shape[1] - 1,
            }
        )
    pd.DataFrame(diagnostic_rows).to_csv(
        dirs.tables / "regression_diagnostics.csv", index=False
    )


def regression_line_with_ci(ax: plt.Axes, x: np.ndarray, y: np.ndarray) -> None:
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    design = np.column_stack([np.ones(len(x)), x])
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    residual = y - design @ beta
    df_resid = len(x) - 2
    mean_squared_error = float(residual @ residual / df_resid)
    grid = np.linspace(np.min(x), np.max(x), 120)
    grid_design = np.column_stack([np.ones_like(grid), grid])
    prediction = grid_design @ beta
    xtx_inverse = np.linalg.pinv(design.T @ design)
    standard_error = np.sqrt(
        np.sum((grid_design @ xtx_inverse) * grid_design, axis=1)
        * mean_squared_error
    )
    critical = stats.t.ppf(0.975, df_resid)
    ax.plot(grid, prediction, color=NEUTRAL, lw=1.35, zorder=2)
    ax.fill_between(
        grid,
        prediction - critical * standard_error,
        prediction + critical * standard_error,
        color=NEUTRAL,
        alpha=0.12,
        lw=0,
        zorder=1,
    )


def plot_adjusted_forest(
    standardized: pd.DataFrame,
    dirs: OutputDirs,
) -> None:
    terms = [f"training_mean_{metric}" for metric in COORDINATION_VARS]
    subset = standardized[standardized["term"].isin(terms)].copy()
    order = [
        "training_mean_lt_rn_count",
        "training_mean_lt_rn_duration_s",
        "training_mean_rt_ln_count",
        "training_mean_rt_ln_duration_s",
    ]
    label_map = {
        "training_mean_lt_rn_count": "LT-RN count",
        "training_mean_lt_rn_duration_s": "LT-RN duration",
        "training_mean_rt_ln_count": "RT-LN count",
        "training_mean_rt_ln_duration_s": "RT-LN duration",
    }
    subset.assign(within_training_metric=subset["term"].map(label_map)).to_csv(
        dirs.source_data / "Fig1_adjusted_associations.csv", index=False
    )

    outcome_order = list(OUTCOME_LABELS.values())
    legend_labels = {
        OUTCOME_LABELS["suture_completion_score"]: "Suture-completion score",
        OUTCOME_LABELS["mean_active_suture_duration_s"]: "Mean suture duration",
    }
    colors = {
        OUTCOME_LABELS["suture_completion_score"]: GROUP_COLORS["uniform"],
        OUTCOME_LABELS["mean_active_suture_duration_s"]: GROUP_COLORS[
            "workload_adapted"
        ],
    }
    markers = {outcome_order[0]: "o", outcome_order[1]: "s"}
    offsets = {outcome_order[0]: 0.12, outcome_order[1]: -0.12}
    y_positions = np.arange(len(order))[::-1]

    fig, ax = plt.subplots(figsize=(5.15, 3.05), constrained_layout=True)
    for outcome in outcome_order:
        for row in subset[subset["model_outcome"] == outcome].itertuples(index=False):
            y_position = y_positions[order.index(row.term)] + offsets[outcome]
            ax.errorbar(
                row.estimate,
                y_position,
                xerr=[[row.estimate - row.ci95_low], [row.ci95_high - row.estimate]],
                color=colors[outcome],
                marker=markers[outcome],
                lw=1.15,
                capsize=2.8,
                markersize=4.2,
                label=legend_labels[outcome],
            )
    ax.axvline(0, color="#7B8085", lw=0.8)
    ax.set_yticks(y_positions)
    ax.set_yticklabels([label_map[item] for item in order])
    ax.set_xlabel("Standardized regression coefficient, β (95% CI)")
    ax.set_title("Adjusted associations", loc="left", fontweight="bold", color=NEUTRAL, pad=11)
    clean_axes(ax)
    ax.grid(axis="x", color=GRID, linewidth=0.5)
    ax.grid(axis="y", visible=False)
    handles, labels = ax.get_legend_handles_labels()
    unique = {}
    for handle, label in zip(handles, labels):
        unique.setdefault(label, handle)
    ax.legend(
        unique.values(),
        unique.keys(),
        frameon=False,
        loc="lower right",
        bbox_to_anchor=(1.0, 1.005),
        ncol=2,
        columnspacing=1.2,
        handlelength=1.7,
    )
    ax.set_xlim(-2.8, 2.9)
    save_figure(fig, dirs.figures / "Fig1_adjusted_associations")
    plt.close(fig)


def plot_transfer_scatter(
    participant: pd.DataFrame,
    primary: pd.DataFrame,
    dirs: OutputDirs,
) -> None:
    x_column = "training_mean_lt_rn_count"
    panels = [
        (
            "a",
            "Suture-completion score",
            "post_transfer_mean_suture_completion_score",
            OUTCOME_LABELS["suture_completion_score"],
            "Suture-completion score",
            3,
        ),
        (
            "b",
            "Mean active suture duration",
            "post_transfer_mean_mean_active_suture_duration_s",
            OUTCOME_LABELS["mean_active_suture_duration_s"],
            "Duration (s/equivalent suture)",
            2,
        ),
    ]
    participant[
        [
            "participant_id",
            "group",
            x_column,
            panels[0][2],
            panels[1][2],
        ]
    ].to_csv(dirs.source_data / "Fig2_LT_RN_transfer_associations.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(7.15, 2.95), constrained_layout=True)
    for ax, panel in zip(axes, panels):
        letter, title, y_column, outcome_label, y_label, decimals = panel
        for group, subset in participant.groupby("group"):
            ax.scatter(
                subset[x_column],
                subset[y_column],
                s=26,
                color=GROUP_COLORS[group],
                alpha=0.9,
                edgecolor="white",
                linewidth=0.55,
                label=GROUP_LABELS[group],
                zorder=3,
            )
        regression_line_with_ci(
            ax,
            participant[x_column].to_numpy(float),
            participant[y_column].to_numpy(float),
        )
        row = term_row(primary, outcome_label, x_column)
        annotation = (
            f"adjusted B={row['estimate']:.{decimals}f}\n"
            f"95% CI {row['ci95_low']:.{decimals}f} to {row['ci95_high']:.{decimals}f}\n"
            f"P={p_text(row['p_value'])}".replace("P=<", "P<")
        )
        ax.text(
            0.03,
            0.97,
            annotation,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=6.6,
            color="#3B4045",
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "white",
                "edgecolor": "#D8DDE1",
                "linewidth": 0.5,
            },
        )
        add_panel_label(ax, letter)
        clean_axes(ax)
        ax.set_title(title, loc="left", fontweight="bold", color=NEUTRAL, pad=5)
        ax.set_xlabel("Within-training mean LT-RN count")
        ax.set_ylabel(y_label)
        ax.margins(x=0.09, y=0.14)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.53, 1.04),
        ncol=2,
        columnspacing=1.2,
        handlelength=1.5,
    )
    save_figure(fig, dirs.figures / "Fig2_LT_RN_transfer_associations")
    plt.close(fig)


def plot_lt_rn_trajectory(
    summary: pd.DataFrame,
    longitudinal: pd.DataFrame,
    stage: str,
    dirs: OutputDirs,
) -> None:
    occasions = OCCASION_ORDER[stage]
    subset = summary[
        (summary["stage"] == stage) & (summary["metric"] == "lt_rn_count")
    ].copy()
    subset["occasion"] = pd.Categorical(
        subset["occasion"], categories=occasions, ordered=True
    )
    subset = subset.sort_values(["group", "occasion"])
    figure_number = 3 if stage == "transfer" else 4
    subset.to_csv(
        dirs.source_data / f"Fig{figure_number}_{stage}_LT_RN_count.csv", index=False
    )

    fig, ax = plt.subplots(figsize=(3.65, 2.65), constrained_layout=True)
    x = np.arange(len(occasions), dtype=float)
    for group, offset in (("uniform", -0.04), ("workload_adapted", 0.04)):
        group_data = subset[subset["group"] == group].sort_values("occasion")
        mean = group_data["mean"].to_numpy(float)
        low = group_data["ci95_low"].to_numpy(float)
        high = group_data["ci95_high"].to_numpy(float)
        ax.errorbar(
            x + offset,
            mean,
            yerr=np.vstack([mean - low, high - mean]),
            color=GROUP_COLORS[group],
            marker="o",
            markersize=4.0,
            lw=1.6,
            elinewidth=1.0,
            capsize=2.8,
            markeredgecolor="white",
            markeredgewidth=0.45,
            label=GROUP_LABELS[group],
            zorder=3,
        )
    occasion = longitudinal_row(longitudinal, stage, "lt_rn_count", "Occasion")
    interaction = longitudinal_row(
        longitudinal, stage, "lt_rn_count", "Group x occasion"
    )
    stat_text = (
        f"occasion: χ²({int(occasion['df'])})={occasion['chi_square']:.2f}, "
        f"P={p_text(occasion['p_value'])}; interaction: P={p_text(interaction['p_value'])}"
    ).replace("P=<", "P<")
    ax.text(
        0.02,
        0.96,
        stat_text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.2,
        color="#4A4F54",
    )
    clean_axes(ax)
    title = "Transfer-test LT-RN count" if stage == "transfer" else "Training-session LT-RN count"
    ax.set_title(title, loc="left", fontweight="bold", color=NEUTRAL, pad=5)
    ax.set_xticks(x)
    ax.set_xticklabels([OCCASION_LABELS[value] for value in occasions])
    ax.set_ylabel("Occurrences")
    ax.margins(x=0.08, y=0.18)
    ax.legend(frameon=False, loc="lower left", handlelength=1.4)
    save_figure(fig, dirs.figures / f"Fig{figure_number}_{stage}_LT_RN_count")
    plt.close(fig)


def create_figures(
    participant: pd.DataFrame,
    models: dict[str, pd.DataFrame],
    summary: pd.DataFrame,
    longitudinal: pd.DataFrame,
    dirs: OutputDirs,
) -> None:
    plot_adjusted_forest(models["standardized"], dirs)
    plot_transfer_scatter(participant, models["primary"], dirs)
    plot_lt_rn_trajectory(summary, longitudinal, "transfer", dirs)
    plot_lt_rn_trajectory(summary, longitudinal, "training", dirs)
