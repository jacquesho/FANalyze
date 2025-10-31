#!/usr/bin/env python3
"""
Export Setlist.fm historical shows to CSV and enrich in-place.

Outputs: data/raw/csv/shows_history.csv

Steps:
1) Fetch all configured artists' setlists via SetlistFMAPI
2) Write CSV with API fields only
3) Enrich CSV in-place with synthetic ticket metrics
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, date, timedelta

import pandas as pd
from rich.console import Console

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.data_collection.setlistfm_api import SetlistFMAPI


console = Console()


def _safe_get(d: Dict[str, Any], path: List[str], default: str = "") -> str:
    cur: Any = d
    for key in path:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return default
    return cur if isinstance(cur, str) else (str(cur) if cur is not None else default)


def _build_show_rows_csv(artist_name: str, artist_id: str, setlists: List[Dict[str, Any]], since_date: Optional[date] = None):
    rows = []
    for sl in setlists:
        show_id = _safe_get(sl, ["id"])  # setlist id
        show_date = _safe_get(sl, ["eventDate"])  # DD-MM-YYYY
        venue_name = _safe_get(sl, ["venue", "name"])
        venue_id = _safe_get(sl, ["venue", "id"])  # may be empty
        city_name = _safe_get(sl, ["venue", "city", "name"])
        state_code = _safe_get(sl, ["venue", "city", "stateCode"])  # may be empty/non-US
        country_name = _safe_get(sl, ["venue", "city", "country", "name"])

        # Filter by since_date if provided
        if since_date and show_date:
            try:
                show_dt = datetime.strptime(show_date, "%d-%m-%Y").date()
                if show_dt < since_date:
                    continue
            except ValueError:
                # If parse fails, let it pass
                pass

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
    columns = [
        "ARTIST_ID", "ARTIST_NAME", "SHOW_ID", "SHOW_DATE", "SOURCE",
        "VENUE_NAME", "VENUE_ID", "CITY_NAME", "STATE_CODE", "COUNTRY_NAME",
    ]
    df = df[columns]
    df.to_csv(csv_path, index=False)
    return csv_path


def _enrich_csv_in_place(csv_path: Path) -> None:
    from scripts.enrich_history_from_setlistfm import enrich_frame  # reuse existing logic
    df = pd.read_csv(csv_path)
    enriched = enrich_frame(df)
    enriched.to_csv(csv_path, index=False)


def main() -> bool:
    console.print("🚀 Exporting SetlistFM history to CSV", style="bold blue")
    # Args
    import argparse
    parser = argparse.ArgumentParser(description="Export SetlistFM history to CSV (with enrichment)")
    parser.add_argument("--since", default="2015-01-01", help="Only include shows on/after this date (YYYY-MM-DD)")
    parser.add_argument("--until", default=None, help="Only include shows on/before this date (YYYY-MM-DD). Default: today")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional max pages per artist to fetch")
    args = parser.parse_args()

    try:
        since_date = datetime.strptime(args.since, "%Y-%m-%d").date()
    except ValueError:
        console.print(f"❌ Invalid --since date format: {args.since} (expected YYYY-MM-DD)", style="red")
        return False

    until_date: Optional[date] = None
    if args.until:
        try:
            until_date = datetime.strptime(args.until, "%Y-%m-%d").date()
        except ValueError:
            console.print(f"❌ Invalid --until date format: {args.until} (expected YYYY-MM-DD)", style="red")
            return False
    api = SetlistFMAPI()
    all_artists = api.artist_config.get_active_artists()

    all_rows: List[Dict[str, Any]] = []
    for artist in all_artists:
        console.print(f"\n🎵 Fetching artist: {artist.name}", style="cyan")
        # Use windowed API (server-side date filtering) with optional page cap
        end_dt = datetime.combine((until_date or datetime.now().date()), datetime.min.time())
        setlists = api.fetch_artist_setlists_window(
            artist,
            since_date=datetime.combine(since_date, datetime.min.time()),
            end_date=end_dt,
            max_pages=args.max_pages,
        )
        show_rows = _build_show_rows_csv(artist.name, artist.musicbrainz_id, setlists, since_date=since_date)
        all_rows.extend(show_rows)

    csv_path = PROJECT_ROOT / "data" / "raw" / "csv" / "shows_history.csv"
    _write_csv(all_rows, csv_path)
    window_desc = f"since {since_date.isoformat()}"
    if until_date:
        window_desc += f" to {until_date.isoformat()}"
    console.print(f"💾 Wrote CSV: {csv_path} ({window_desc}, rows={len(all_rows)})", style="green")

    _enrich_csv_in_place(csv_path)
    console.print("✨ Enriched CSV in-place with synthetic ticket metrics", style="green")
    return True


if __name__ == "__main__":
    ok = main()
    raise SystemExit(0 if ok else 1)


