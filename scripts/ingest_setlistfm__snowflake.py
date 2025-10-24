#!/usr/bin/env python3
"""
End-to-end ingestion for SetlistFM → Snowflake (testing schema)

Pipeline steps:
1) Ensure Snowflake testing tables exist (DDL)
2) For each active artist in config:
   - Fetch all setlists (paginated)
   - Build shows and setlists JSON rows
3) Load rows into testing.raw_shows and testing.raw_setlists
"""
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import unicodedata
import re
from rich.console import Console
from dotenv import load_dotenv
from pathlib import Path

# Ensure project root is on sys.path so `scripts.*` imports resolve when run directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.data_collection.setlistfm_api import SetlistFMAPI
from scripts.database.sf_loader import ensure_testing_tables, get_snowflake_connection

load_dotenv()
console = Console()


def _build_show_rows(artist_name: str, artist_id: str, setlists: List[Dict[str, Any]]):
    rows = []
    for sl in setlists:
        show_id = sl.get("id")
        show_date = sl.get("eventDate")  # DD-MM-YYYY
        # Keep raw JSON as string for VARIANT
        rows.append(
            {
                "artist_id": artist_id,
                "artist_name": artist_name,
                "show_id": show_id,
                "show_date": show_date,
                "payload_json": json.dumps(sl),
            }
        )
    return rows


def _write_jsonl(files_dir: Path, artist_slug: str, rows: List[Dict[str, Any]]) -> Path:
    """Write rows as JSON Lines to a file for staging."""
    files_dir.mkdir(parents=True, exist_ok=True)
    out_path = files_dir / f"{artist_slug}_shows.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return out_path


def _slugify(text: str) -> str:
    """ASCII slug for filenames/stage paths: letters, numbers, underscores only."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Za-z0-9]+", "_", normalized).strip("_").lower()
    return slug or "artist"


def _has_artist_loaded(artist_id: str) -> bool:
    """Check if artist already has rows in testing.raw_shows (for resume support)."""
    conn = get_snowflake_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM testing.raw_shows WHERE artist_id=%s", (artist_id,))
            (cnt,) = cur.fetchone()
            return int(cnt) > 0
    finally:
        conn.close()


def main() -> bool:
    console.print("🚀 SetlistFM → Snowflake (testing) Ingestion", style="bold blue")

    # 1) Ensure DDL (resolve relative to project root regardless of CWD)
    ddl_file = PROJECT_ROOT / "sql" / "init_setlistfm_testing.sql"
    ensure_testing_tables(ddl_file)

    # 2) Extract
    api = SetlistFMAPI()
    all_artists = api.artist_config.get_active_artists()

    # Local staging directory for JSONL files
    staging_dir = PROJECT_ROOT / "data" / "external" / "staging_json"

    for artist in all_artists:
        console.print(f"\n🎵 Fetching artist: {artist.name}", style="cyan")

        # Resume: skip if already loaded
        if _has_artist_loaded(artist.musicbrainz_id):
            console.print("   • Detected existing rows in testing.raw_shows, skipping fetch/load", style="yellow")
            continue
        # Full-history fetch per artist
        setlists = api.fetch_artist_setlists(artist, artist.starting_tour)

        show_rows = _build_show_rows(artist.name, artist.musicbrainz_id, setlists)
        # 3) Write per-artist JSONL and stage to Snowflake
        artist_slug = _slugify(artist.name)
        jsonl_path = _write_jsonl(staging_dir, artist_slug, show_rows)

        conn = get_snowflake_connection()
        cur = conn.cursor()
        try:
            console.print(f"   • PUT {jsonl_path} to @testing.stage_raw_json", style="dim")
            local_path = jsonl_path.as_posix()
            cur.execute(f"PUT 'file://{local_path}' @testing.stage_raw_json AUTO_COMPRESS=FALSE OVERWRITE=TRUE")

            console.print("   • COPY INTO testing.raw_shows from stage", style="dim")
            stage_file_name = jsonl_path.name
            cur.execute(
                "COPY INTO testing.raw_shows (artist_id, artist_name, show_id, show_date, payload) "
                "FROM (\n"
                "  SELECT\n"
                "    $1:artist_id::string,\n"
                "    $1:artist_name::string,\n"
                "    $1:show_id::string,\n"
                "    TO_DATE($1:show_date::string, 'DD-MM-YYYY'),\n"
                "    $1\n"
                f"  FROM '@testing.stage_raw_json/{stage_file_name}' (FILE_FORMAT => testing.ff_json)\n"
                ")"
            )
        finally:
            cur.close()
            conn.close()

    console.print("\n✅ Completed COPY INTO for all artists", style="green")
    return True


if __name__ == "__main__":
    ok = main()
    raise SystemExit(0 if ok else 1)


