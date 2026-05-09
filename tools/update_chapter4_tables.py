#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate LaTeX row blocks for Chapter 4 tables (Section 4.2.x) from experiment CSV data."""

import argparse
import os
from datetime import datetime
from typing import Dict, Optional

import pandas as pd


ALGORITHM_ORDER = [
    "Proposed",
    "Rule-based (Greedy)",
    "CBS-based",
    "Auction-based",
]

ALGORITHM_FAMILY_ALIAS = {
    "full": "Proposed",
    "proposed": "Proposed",
    "naive": "Rule-based (Greedy)",
    "rule_greedy": "Rule-based (Greedy)",
    "path_reservation": "CBS-based",
    "cbs_based": "CBS-based",
    "path_only": "Auction-based",
    "auction_based": "Auction-based",
    "本系统": "Proposed",
}

PLACEHOLDER = "[To be filled]"


def _safe_float(value: object) -> Optional[float]:
    try:
        if value is None:
            return None
        f = float(value)
        if pd.isna(f):
            return None
        return f
    except Exception:
        return None


def _fmt_percent(value: Optional[float], decimals: int = 2) -> str:
    if value is None:
        return PLACEHOLDER
    return f"{value:.{decimals}f}\\%"


def _fmt_float(value: Optional[float], decimals: int = 3) -> str:
    if value is None:
        return PLACEHOLDER
    return f"{value:.{decimals}f}"


def _fmt_int(value: Optional[float]) -> str:
    if value is None:
        return PLACEHOLDER
    return str(int(round(value)))


def _wrap_bold(text: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"\\textbf{{{text}}}"


def _row_label(family: str) -> str:
    if family == "Proposed":
        return "\\textbf{Proposed}"
    return family


def load_standard_summary(source_file: str, preferred_mode: str) -> Dict[str, Dict[str, Optional[float]]]:
    """Load algorithm_comparison_summary.csv and aggregate by algorithm family."""
    if not os.path.exists(source_file):
        return {}

    df = pd.read_csv(source_file)
    if df.empty:
        return {}

    if "algorithm_family" not in df.columns:
        mode_col = "algorithm_mode_normalized" if "algorithm_mode_normalized" in df.columns else "algorithm_mode"
        if mode_col in df.columns:
            df["algorithm_family"] = df[mode_col].astype(str).str.strip().str.lower().map(ALGORITHM_FAMILY_ALIAS)
        else:
            return {}

    if "algorithm_family" not in df.columns:
        return {}

    df = df[df["algorithm_family"].isin(ALGORITHM_ORDER)].copy()
    if df.empty:
        return {}

    mode_col = "experiment_mode_normalized" if "experiment_mode_normalized" in df.columns else "experiment_mode"
    preferred_subset = df
    if mode_col in df.columns:
        preferred_subset = df[df[mode_col].astype(str).str.strip().str.lower() == preferred_mode.lower()].copy()

    if not preferred_subset.empty:
        working = preferred_subset
    else:
        working = df

    metric_cols = [
        "task_completion_rate_pct",
        "makespan_s",
        "throughput_tasks_per_min",
        "deadlock_count",
        "deadlock_resolution_ratio",
        "collision_count",
        "total_travel_distance_m",
        "load_balance_gini",
    ]

    for col in metric_cols:
        if col in working.columns:
            working[col] = pd.to_numeric(working[col], errors="coerce")

    grouped = working.groupby("algorithm_family", as_index=False)[metric_cols].mean(numeric_only=True)

    result: Dict[str, Dict[str, Optional[float]]] = {}
    for _, row in grouped.iterrows():
        family = str(row["algorithm_family"])
        result[family] = {
            "task_completion_rate_pct": _safe_float(row.get("task_completion_rate_pct")),
            "makespan_s": _safe_float(row.get("makespan_s")),
            "throughput_tasks_per_min": _safe_float(row.get("throughput_tasks_per_min")),
            "deadlock_count": _safe_float(row.get("deadlock_count")),
            "deadlock_resolution_ratio": _safe_float(row.get("deadlock_resolution_ratio")),
            "collision_count": _safe_float(row.get("collision_count")),
            "total_travel_distance_m": _safe_float(row.get("total_travel_distance_m")),
            "load_balance_gini": _safe_float(row.get("load_balance_gini")),
        }

    return result


def load_legacy_summary(legacy_file: str) -> Dict[str, Dict[str, Optional[float]]]:
    """Load legacy comparison CSV (partial metrics only)."""
    if not os.path.exists(legacy_file):
        return {}

    df = pd.read_csv(legacy_file)
    if df.empty:
        return {}

    if "方案" not in df.columns:
        return {}

    result: Dict[str, Dict[str, Optional[float]]] = {}
    for _, row in df.iterrows():
        raw_name = str(row.get("方案", "")).strip()
        family = ALGORITHM_FAMILY_ALIAS.get(raw_name, raw_name)
        if family not in ALGORITHM_ORDER:
            continue

        completion_min = _safe_float(row.get("完成时间(min)"))
        deadlock_count = _safe_float(row.get("死锁次数"))
        collision_count = _safe_float(row.get("碰撞次数"))

        result[family] = {
            "task_completion_rate_pct": None,
            "makespan_s": completion_min * 60.0 if completion_min is not None else None,
            "throughput_tasks_per_min": None,
            "deadlock_count": deadlock_count,
            "deadlock_resolution_ratio": None,
            "collision_count": collision_count,
            "total_travel_distance_m": None,
            "load_balance_gini": None,
        }

    return result


def render_rows(metric_map: Dict[str, Dict[str, Optional[float]]]) -> Dict[str, str]:
    rows_422 = []
    rows_423 = []

    for family in ALGORITHM_ORDER:
        values = metric_map.get(family, {})
        is_proposed = family == "Proposed"
        label = _row_label(family)

        completion_rate = _wrap_bold(_fmt_percent(values.get("task_completion_rate_pct")), is_proposed)
        makespan = _wrap_bold(_fmt_float(values.get("makespan_s"), 2), is_proposed)
        throughput = _wrap_bold(_fmt_float(values.get("throughput_tasks_per_min"), 3), is_proposed)
        distance = _wrap_bold(_fmt_float(values.get("total_travel_distance_m"), 2), is_proposed)
        gini = _wrap_bold(_fmt_float(values.get("load_balance_gini"), 4), is_proposed)

        deadlock = _wrap_bold(_fmt_int(values.get("deadlock_count")), is_proposed)
        deadlock_ratio = _wrap_bold(_fmt_float(values.get("deadlock_resolution_ratio"), 4), is_proposed)
        collision = _wrap_bold(_fmt_int(values.get("collision_count")), is_proposed)

        rows_422.append(
            f"{label} & {completion_rate} & {makespan} & {throughput} & {distance} & {gini} \\\\"
        )
        rows_423.append(
            f"{label} & {deadlock} & {deadlock_ratio} & {collision} \\\\"
        )

    return {
        "table_422_rows": "\n".join(rows_422),
        "table_423_rows": "\n".join(rows_423),
    }


def write_latex_row_file(output_file: str, rendered_rows: Dict[str, str], source_note: str) -> None:
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    content = (
        "% Auto-generated by tools/update_chapter4_tables.py\n"
        f"% Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"% Source: {source_note}\n\n"
        "\\newcommand{\\TableFourTwoTwoRows}{\n"
        f"{rendered_rows['table_422_rows']}\n"
        "}\n\n"
        "\\newcommand{\\TableFourTwoThreeRows}{\n"
        f"{rendered_rows['table_423_rows']}\n"
        "}\n"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Chapter 4 table row macros from exported experiment metrics")
    parser.add_argument(
        "--source",
        default="paper_materials/algorithm_comparison_summary.csv",
        help="Primary CSV source (recommended: algorithm_comparison_summary.csv)",
    )
    parser.add_argument(
        "--legacy-source",
        default="paper_materials/表2_算法对比数据.csv",
        help="Legacy fallback CSV source",
    )
    parser.add_argument(
        "--mode",
        default="stress",
        help="Preferred experiment mode for aggregation (default: stress)",
    )
    parser.add_argument(
        "--output",
        default="paper_materials/chapter4_table_421_rows.tex",
        help="Output LaTeX row macro file",
    )
    args = parser.parse_args()

    metric_map = load_standard_summary(args.source, args.mode)
    source_note = args.source

    if not metric_map:
        metric_map = load_legacy_summary(args.legacy_source)
        source_note = f"legacy fallback: {args.legacy_source}"

    rendered_rows = render_rows(metric_map)
    write_latex_row_file(args.output, rendered_rows, source_note)

    print("Generated Chapter 4 row macro file:")
    print(f"  - {args.output}")
    print(f"  - Preferred mode: {args.mode}")
    print(f"  - Source used: {source_note}")

    filled_families = [k for k, v in metric_map.items() if any(val is not None for val in v.values())]
    if filled_families:
        print("  - Families with data: " + ", ".join(sorted(filled_families)))
    else:
        print("  - No numeric source rows detected; placeholders were kept")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
