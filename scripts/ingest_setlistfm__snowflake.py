#!/usr/bin/env python3
"""
Load shows_history.csv into Snowflake (CSV-only path).

Usage:
  # Ensure CSV exists first (run export_setlistfm_history_to_csv.py)
  uv run python scripts/ingest_setlistfm__snowflake.py

Set LOAD_TO_SNOWFLAKE=true to enable load (default enabled).
"""
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List
import unicodedata
import re
from rich.console import Console
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd

# Ensure project root is on sys.path so `scripts.*` imports resolve when run directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.data_collection.setlistfm_api import SetlistFMAPI
# Optional CSV → Snowflake loader
try:
    from scripts.ingest_csv_shows__snowflake import ingest_csv_to_snowflake
except Exception:
    ingest_csv_to_snowflake = None

load_dotenv()
console = Console()


def _safe_get(d: Dict[str, Any], path: List[str], default: str = "") -> str:
    cur: Any = d
    for key in path:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return default
    return cur if isinstance(cur, str) else (str(cur) if cur is not None else default)


def _build_show_rows_csv(artist_name: str, artist_id: str, setlists: List[Dict[str, Any]]):
    rows = []
    for sl in setlists:
        show_id = _safe_get(sl, ["id"])  # setlist id
        show_date = _safe_get(sl, ["eventDate"])  # DD-MM-YYYY
        venue_name = _safe_get(sl, ["venue", "name"])
        venue_id = _safe_get(sl, ["venue", "id"])  # may be empty
        city_name = _safe_get(sl, ["venue", "city", "name"])
        state_code = _safe_get(sl, ["venue", "city", "stateCode"])  # may be empty/non-US
        country_name = _safe_get(sl, ["venue", "city", "country", "name"])

        rows.append(
            {
                "ARTIST_ID": artist_id,
                "ARTIST_NAME": artist_name,
                "SHOW_ID": show_id,
                "SHOW_DATE": show_date,
                "SOURCE": "setlist.fm",
                "VENUE_NAME": venue_name,
                "VENUE_ID": venue_id,
                "CITY_NAME": city_name,
                "STATE_CODE": state_code,
                "COUNTRY_NAME": country_name,
            }
        )
    return rows


def _write_csv(all_rows: List[Dict[str, Any]], csv_path: Path) -> Path:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(all_rows)
    # Ensure column order
    columns = [
        "ARTIST_ID", "ARTIST_NAME", "SHOW_ID", "SHOW_DATE", "SOURCE",
        "VENUE_NAME", "VENUE_ID", "CITY_NAME", "STATE_CODE", "COUNTRY_NAME",
    ]
    df = df[columns]
    df.to_csv(csv_path, index=False)
    return csv_path


def _slugify(text: str) -> str:
    """ASCII slug for filenames/stage paths: letters, numbers, underscores only."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Za-z0-9]+", "_", normalized).strip("_").lower()
    return slug or "artist"


def _enrich_csv_in_place(csv_path: Path) -> None:
    """Load CSV, enrich with synthetic metrics, overwrite same file."""
    from scripts.enrich_history_from_setlistfm import enrich_frame  # reuse existing logic
    df = pd.read_csv(csv_path)
    enriched = enrich_frame(df)
    enriched.to_csv(csv_path, index=False)


def main(load_to_snowflake: bool = True) -> bool:
    console.print("🚀 CSV → Snowflake (SHOWS_HIS)", style="bold blue")
    csv_path = PROJECT_ROOT / "data" / "raw" / "csv" / "shows_history.csv"
    if not csv_path.exists():
        console.print(f"❌ CSV not found: {csv_path}", style="red")
        console.print("Run scripts/export_setlistfm_history_to_csv.py first.", style="yellow")
        return False

    if ingest_csv_to_snowflake is None:
        console.print("❌ CSV ingester not available", style="red")
        return False

    if load_to_snowflake:
        ok = ingest_csv_to_snowflake(str(csv_path), "SHOWS_HIS")
        console.print("❄️  Loaded to Snowflake SHOWS_HIS" if ok else "⚠️  Snowflake load failed", style=("green" if ok else "yellow"))
        return ok
    else:
        console.print("ℹ️  LOAD_TO_SNOWFLAKE disabled; skipping load.", style="yellow")
        return True


if __name__ == "__main__":
    # Default load to Snowflake unless explicitly disabled
    load_sf = os.getenv("LOAD_TO_SNOWFLAKE", "true").lower() in {"1", "true", "yes"}
    ok = main(load_to_snowflake=load_sf)
    raise SystemExit(0 if ok else 1)


