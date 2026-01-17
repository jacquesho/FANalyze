#!/usr/bin/env python3
"""
Export Setlist.fm historical shows to CSV and enrich in-place.

Outputs: data/raw/csv/shows_history.csv

Steps:
1) Fetch configured artists' setlists via SetlistFMAPI
2) Write CSV with API fields only
3) Enrich CSV in-place with synthetic ticket metrics (unless --no-enrich)

Modes:
- Default: Date-based filtering (all shows since --since date)
- Batch mode (--batch): Fetch N most recent shows per artist (default: 100)
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, date

import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

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


def _build_show_rows_csv(
    artist_name: str,
    artist_id: str,
    setlists: List[Dict[str, Any]],
    since_date: Optional[date] = None,
):
    rows = []
    for sl in setlists:
        show_id = _safe_get(sl, ["id"])  # setlist id
        show_date = _safe_get(sl, ["eventDate"])  # DD-MM-YYYY
        venue_name = _safe_get(sl, ["venue", "name"])
        venue_id = _safe_get(sl, ["venue", "id"])  # may be empty
        city_name = _safe_get(sl, ["venue", "city", "name"])
        state_code = _safe_get(
            sl, ["venue", "city", "stateCode"]
        )  # may be empty/non-US
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
        "ARTIST_ID",
        "ARTIST_NAME",
        "SHOW_ID",
        "SHOW_DATE",
        "SOURCE",
        "VENUE_NAME",
        "VENUE_ID",
        "CITY_NAME",
        "STATE_CODE",
        "COUNTRY_NAME",
    ]
    df = df[columns]
    df.to_csv(csv_path, index=False)
    return csv_path


def _fetch_most_recent_shows(
    api: SetlistFMAPI, artist, max_shows: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch the most recent N shows for an artist.
    The API returns shows in reverse chronological order (most recent first).
    Stops early when max_shows is reached to optimize API calls.
    """
    all_shows = []
    page = 1

    console.print(
        f"🎵 Fetching up to {max_shows} most recent shows for {artist.name}",
        style="blue",
    )

    while len(all_shows) < max_shows:
        url = api.config.get_artist_setlists_url(artist.musicbrainz_id, page)

        try:
            response = api.make_api_request_with_retry(url)
        except Exception as e:
            console.print(
                f"❌ Request failed for {artist.name} page {page}: {e}", style="red"
            )
            break

        if response.status_code != 200:
            console.print(
                f"❌ Error fetching page {page} for {artist.name}: {response.status_code}",
                style="red",
            )
            break

        data = response.json()
        setlists = data.get("setlist", [])

        if not setlists:
            console.print(f"✅ No more setlists found on page {page}", style="green")
            break

        # Add shows until we reach max_shows
        remaining = max_shows - len(all_shows)
        all_shows.extend(setlists[:remaining])

        console.print(
            f"✅ Fetched {len(setlists)} shows from page {page} "
            f"(total: {len(all_shows)}/{max_shows})",
            style="green",
        )

        # Check if we've reached our target
        if len(all_shows) >= max_shows:
            break

        # Check if there are more pages
        if page == 1:
            total_items = int(data.get("total", 0))
            if total_items < max_shows:
                console.print(
                    f"⚠️ Artist {artist.name} only has {total_items} total shows "
                    f"(requested {max_shows})",
                    style="yellow",
                )

        page += 1
        time.sleep(api.config.rate_limit_delay)

    # Trim to exactly max_shows if we got more
    return all_shows[:max_shows]


def _enrich_csv_in_place(csv_path: Path) -> None:
    from scripts.enrich_history_from_setlistfm import (
        enrich_frame,
    )  # reuse existing logic

    df = pd.read_csv(csv_path)
    enriched = enrich_frame(df)
    enriched.to_csv(csv_path, index=False)


def main() -> bool:
    console.print("🚀 Exporting SetlistFM history to CSV", style="bold blue")
    # Args
    import argparse

    parser = argparse.ArgumentParser(
        description="Export SetlistFM history to CSV (with enrichment)"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Batch mode: fetch N most recent shows per artist (default: 100). Uses all artists.",
    )
    parser.add_argument(
        "--max-shows-per-artist",
        type=int,
        default=100,
        help="In batch mode: max shows per artist (default: 100). Ignored if --batch not set.",
    )
    parser.add_argument(
        "--since",
        default="2015-01-01",
        help="Only include shows on/after this date (YYYY-MM-DD). Ignored in batch mode.",
    )
    parser.add_argument(
        "--until",
        default=None,
        help="Only include shows on/before this date (YYYY-MM-DD). Default: today. Ignored in batch mode.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional max pages per artist to fetch (date-based mode only)",
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip CSV enrichment with synthetic ticket metrics",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output filename (without .csv extension). Default: shows_history.csv",
    )
    args = parser.parse_args()

    api = SetlistFMAPI()

    # Determine which artists to use
    if args.batch:
        # Batch mode: use all artists
        all_artists = api.artist_config.artists
        console.print(
            f"📊 Batch mode: Fetching {args.max_shows_per_artist} most recent shows "
            f"for {len(all_artists)} artists",
            style="cyan",
        )
    else:
        # Date-based mode: use active artists only
        all_artists = api.artist_config.get_active_artists()
        try:
            since_date = datetime.strptime(args.since, "%Y-%m-%d").date()
        except ValueError:
            console.print(
                f"❌ Invalid --since date format: {args.since} (expected YYYY-MM-DD)",
                style="red",
            )
            return False

        until_date: Optional[date] = None
        if args.until:
            try:
                until_date = datetime.strptime(args.until, "%Y-%m-%d").date()
            except ValueError:
                console.print(
                    f"❌ Invalid --until date format: {args.until} (expected YYYY-MM-DD)",
                    style="red",
                )
                return False

    all_rows: List[Dict[str, Any]] = []

    # Fetch shows based on mode
    if args.batch:
        # Batch mode: fetch most recent N shows per artist
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Fetching shows for all artists...", total=len(all_artists)
            )

            for artist in all_artists:
                progress.update(task, description=f"Fetching {artist.name}...")

                try:
                    setlists = _fetch_most_recent_shows(
                        api, artist, max_shows=args.max_shows_per_artist
                    )
                    show_rows = _build_show_rows_csv(
                        artist.name, artist.musicbrainz_id, setlists
                    )
                    all_rows.extend(show_rows)

                    console.print(
                        f"✅ {artist.name}: {len(show_rows)} shows collected",
                        style="green",
                    )
                except Exception as e:
                    console.print(
                        f"❌ Failed to fetch data for {artist.name}: {e}", style="red"
                    )

                progress.advance(task)

    else:
        # Date-based mode: use existing logic
        for artist in all_artists:
            console.print(f"\n🎵 Fetching artist: {artist.name}", style="cyan")
            # Use windowed API (server-side date filtering) with optional page cap
            end_dt = datetime.combine(
                (until_date or datetime.now().date()), datetime.min.time()
            )
            setlists = api.fetch_artist_setlists_window(
                artist,
                since_date=datetime.combine(since_date, datetime.min.time()),
                end_date=end_dt,
                max_pages=args.max_pages,
            )
            show_rows = _build_show_rows_csv(
                artist.name, artist.musicbrainz_id, setlists, since_date=since_date
            )
            all_rows.extend(show_rows)

    # Use default filename (or custom if specified)
    csv_filename = args.output + ".csv" if args.output else "shows_history.csv"

    csv_path = PROJECT_ROOT / "data" / "raw" / "csv" / csv_filename
    _write_csv(all_rows, csv_path)

    # Print summary
    if args.batch:
        console.print(
            f"💾 Batch dataset saved: {csv_path} ({len(all_rows)} rows)",
            style="green",
        )
        # Show breakdown by artist
        if all_rows:
            df = pd.DataFrame(all_rows)
            artist_counts = df["ARTIST_NAME"].value_counts()
            console.print("\n📈 Shows per artist:", style="cyan")
            for artist_name, count in artist_counts.items():
                console.print(f"   {artist_name}: {count} shows", style="cyan")
    else:
        window_desc = f"since {since_date.isoformat()}"
        if until_date:
            window_desc += f" to {until_date.isoformat()}"
        console.print(
            f"💾 Wrote CSV: {csv_path} ({window_desc}, rows={len(all_rows)})",
            style="green",
        )

    # Enrich CSV unless disabled
    if not args.no_enrich:
        _enrich_csv_in_place(csv_path)
        console.print(
            "✨ Enriched CSV in-place with synthetic ticket metrics", style="green"
        )
    else:
        console.print("⏭️  Skipping CSV enrichment (--no-enrich)", style="yellow")

    return True


if __name__ == "__main__":
    ok = main()
    raise SystemExit(0 if ok else 1)
