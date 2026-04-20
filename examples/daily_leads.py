"""Daily tech-recruitment lead generation using JobSpy.

Scrapes fresh job postings across configured verticals x locations, dedupes
against a persistent history of previously-seen job URLs, and writes a dated
CSV of new leads for the BD team.

Usage:
    python examples/daily_leads.py [path/to/config.yaml]

Defaults to examples/leads_config.yaml next to this script.
"""

from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from jobspy import scrape_jobs


PRIORITY_COLUMNS = [
    "site",
    "company",
    "title",
    "location",
    "job_url",
    "company_url",
    "date_posted",
    "job_type",
    "is_remote",
    "min_amount",
    "max_amount",
    "currency",
    "interval",
    "description",
    "search_term",
    "search_location",
]


def load_config(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def load_history(history_file: Path) -> set[str]:
    if not history_file.exists():
        return set()
    df = pd.read_csv(history_file)
    return set(df["job_url"].dropna().astype(str))


def append_history(history_file: Path, new_urls: list[str]) -> None:
    if not new_urls:
        return
    history_file.parent.mkdir(parents=True, exist_ok=True)
    new_df = pd.DataFrame({"job_url": new_urls, "first_seen": date.today().isoformat()})
    if history_file.exists():
        new_df.to_csv(history_file, mode="a", header=False, index=False)
    else:
        new_df.to_csv(history_file, index=False)


def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    present = [c for c in PRIORITY_COLUMNS if c in df.columns]
    rest = [c for c in df.columns if c not in present]
    return df[present + rest]


def run(config_path: Path) -> int:
    cfg = load_config(config_path)

    sites = cfg["sites"]
    verticals = cfg["verticals"]
    locations = cfg["locations"]
    results_wanted = cfg.get("results_wanted", 50)
    hours_old = cfg.get("hours_old", 24)
    country_indeed = cfg.get("country_indeed", "USA")
    description_format = cfg.get("description_format", "markdown")

    output_dir = Path(cfg["output_dir"]).expanduser()
    history_file = Path(cfg["history_file"]).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    history = load_history(history_file)

    frames: list[pd.DataFrame] = []
    total_queries = len(verticals) * len(locations)
    done = 0
    for role in verticals:
        for loc in locations:
            done += 1
            print(f"[{done}/{total_queries}] {role!r} @ {loc!r}", flush=True)
            try:
                df = scrape_jobs(
                    site_name=sites,
                    search_term=role,
                    location=loc,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    country_indeed=country_indeed,
                    description_format=description_format,
                )
            except Exception as exc:
                print(f"  ! failed: {exc}", flush=True)
                continue
            if df is None or df.empty:
                continue
            df = df.copy()
            df["search_term"] = role
            df["search_location"] = loc
            frames.append(df)

    if not frames:
        print("No results returned from any query.", flush=True)
        return 0

    all_today = pd.concat(frames, ignore_index=True)
    all_today = all_today.dropna(subset=["job_url"]).drop_duplicates(subset=["job_url"])

    new_leads = all_today[~all_today["job_url"].astype(str).isin(history)]
    new_leads = reorder_columns(new_leads)

    today = date.today().isoformat()
    out_file = output_dir / f"leads_{today}.csv"
    new_leads.to_csv(
        out_file,
        index=False,
        quoting=csv.QUOTE_NONNUMERIC,
        escapechar="\\",
    )
    append_history(history_file, new_leads["job_url"].astype(str).tolist())

    print(
        f"{len(verticals)} roles x {len(locations)} locations -> "
        f"{len(all_today)} total -> {len(new_leads)} new leads",
        flush=True,
    )
    print(f"Wrote {out_file}", flush=True)
    return len(new_leads)


if __name__ == "__main__":
    default_config = Path(__file__).parent / "leads_config.yaml"
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_config
    run(config_path)
