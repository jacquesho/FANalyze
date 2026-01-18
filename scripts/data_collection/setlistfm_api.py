#!/usr/bin/env python3
"""
SetlistFM API Connection for FANalyze v2.0
Handles API calls to SetlistFM with pagination and rate limiting
"""

import sys
import time
import json
import math
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

# Add config directory to path
sys.path.append(str(Path(__file__).parent.parent.parent / "config"))

from api_config import SetlistFMConfig
from artists_config import Artist, ArtistConfig

console = Console()


class SetlistFMAPI:
    """SetlistFM API connection handler"""

    def __init__(self):
        self.config = SetlistFMConfig()
        self.artist_config = ArtistConfig()

        if not self.config.api_key:
            raise ValueError("SETLISTFM_API_KEY not found in environment variables")

    def make_api_request_with_retry(
        self, url: str, max_retries: int = None
    ) -> requests.Response:
        """Make API request with retry logic for rate limiting"""
        max_retries = max_retries or self.config.max_retries
        base_delay = 5

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url, headers=self.config.headers, timeout=self.config.timeout
                )

                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    # Rate limited - wait with exponential backoff
                    delay = base_delay * (2**attempt)
                    console.print(
                        f"⏳ Rate limited (429). Waiting {delay} seconds before retry {attempt + 1}/{max_retries}",
                        style="yellow",
                    )
                    time.sleep(delay)
                    continue
                else:
                    # Other error - return immediately
                    return response

            except Exception as e:
                console.print(
                    f"❌ Request failed on attempt {attempt + 1}: {str(e)}", style="red"
                )
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    time.sleep(delay)
                    continue
                else:
                    raise e

        # Final attempt without retry
        return requests.get(
            url, headers=self.config.headers, timeout=self.config.timeout
        )

    def fetch_artist_setlists(
        self, artist: Artist, starting_tour: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch all setlists for a given artist from SetlistFM API"""
        all_shows = []
        page = 1
        total_pages = None

        console.print(
            f"🎵 Fetching setlists for {artist.name} (ID: {artist.musicbrainz_id})",
            style="blue",
        )

        while True:
            url = self.config.get_artist_setlists_url(artist.musicbrainz_id, page)
            if starting_tour:
                url += f"&tourName={requests.utils.quote(starting_tour)}"

            console.print(f"📄 Page {page}: {url}", style="cyan")

            try:
                response = self.make_api_request_with_retry(url)
            except requests.RequestException as e:
                console.print(
                    f"❌ Request failed for {artist.name} page {page}: {e}", style="red"
                )
                break

            if response.status_code != 200:
                console.print(
                    f"❌ Error fetching page {page} for {artist.name}: {response.status_code}",
                    style="red",
                )
                console.print(f"Response: {response.text[:200]}...", style="red")
                break

            data = response.json()
            setlists = data.get("setlist", [])

            if not setlists:
                console.print(
                    f"✅ No more setlists found on page {page}, completed",
                    style="green",
                )
                break

            all_shows.extend(setlists)

            # Get total pages from the first response
            if total_pages is None:
                items_per_page = int(data.get("itemsPerPage", 20))
                total = int(data.get("total", 0))
                total_pages = math.ceil(total / items_per_page) if items_per_page else 1
                console.print(
                    f"📊 Total pages for {artist.name}: {total_pages} (Total items: {total})",
                    style="green",
                )

                # If we can't determine total pages, use a fallback strategy
                if total_pages <= 1 and total == 0:
                    console.print(
                        "⚠️ Could not determine total pages, will continue until no more data",
                        style="yellow",
                    )
                    total_pages = float("inf")  # Continue until no more data

            console.print(
                f"✅ Fetched {len(setlists)} shows from page {page} for {artist.name}",
                style="green",
            )
            console.print(
                f"📈 Total shows collected so far: {len(all_shows)}", style="green"
            )

            if page >= total_pages:
                console.print(
                    f"🏁 Reached last page ({page}/{total_pages}), stopping",
                    style="green",
                )
                break

            page += 1
            console.print(
                f"⏳ Waiting {self.config.rate_limit_delay} seconds before next request...",
                style="yellow",
            )
            time.sleep(self.config.rate_limit_delay)

        console.print(
            f"🎉 {artist.name}: {len(all_shows)} shows collected total",
            style="bold green",
        )
        return all_shows

    # City-filtered helper removed per request to fetch full history for each artist.

    def fetch_artist_setlists_incremental(
        self,
        artist: Artist,
        last_show_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch setlists for an artist from a specific date onwards (incremental updates)

        Args:
            artist: Artist configuration
            last_show_date: fetch strictly AFTER this date
            end_date: upper bound date (inclusive). Defaults to today if not provided
            max_pages: optional hard cap on pages fetched to bound execution time
        """
        all_shows = []
        page = 1
        seen_show_ids = set()  # Track show IDs to prevent duplicates

        # Handle date filtering
        if last_show_date is None:
            start_date = (datetime.now() - timedelta(days=30)).date()
            console.print(
                f"📅 No previous shows found for {artist.name}, fetching last 30 days",
                style="yellow",
            )
        else:
            start_date = last_show_date.date() + timedelta(days=1)
            console.print(
                f"📅 Fetching shows for {artist.name} from {start_date} onwards",
                style="blue",
            )

        end_date = (
            end_date.date() if isinstance(end_date, datetime) else end_date
        ) or datetime.now().date()

        console.print(
            f"🎵 Fetching incremental setlists for {artist.name} ({artist.musicbrainz_id})",
            style="blue",
        )
        console.print(f"📅 Date range: {start_date} to {end_date}", style="cyan")

        while True:
            url = self.config.get_artist_setlists_url(artist.musicbrainz_id, page)

            # Add date filtering to reduce API response size
            start_date_str = start_date.strftime("%d-%m-%Y")
            end_date_str = end_date.strftime("%d-%m-%Y")
            url += f"&date={start_date_str}-{end_date_str}"

            console.print(f"📄 Page {page}: {url}", style="cyan")

            try:
                response = self.make_api_request_with_retry(url)
            except requests.RequestException as e:
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
            setlist_items = data.get("setlist", [])

            if not setlist_items:
                console.print(
                    f"✅ No more setlists found on page {page}, completed",
                    style="green",
                )
                break

            # Filter shows by date and deduplicate
            for show in setlist_items:
                show_date_str = show.get("eventDate", "")
                if show_date_str:
                    try:
                        # Parse the show date (format: DD-MM-YYYY)
                        show_date = datetime.strptime(show_date_str, "%d-%m-%Y").date()

                        # Only include shows strictly after the last show date to avoid duplicates
                        if last_show_date is None or show_date > last_show_date.date():
                            show_id = show.get("id")
                            if show_id and show_id not in seen_show_ids:
                                all_shows.append(show)
                                seen_show_ids.add(show_id)
                    except ValueError:
                        # If we can't parse the date, skip this show
                        pass

            # Get total pages from the first response
            if page == 1:
                items_per_page = int(data.get("itemsPerPage", 20))
                total = int(data.get("total", 0))
                total_pages = math.ceil(total / items_per_page) if items_per_page else 1
                console.print(
                    f"📊 Total pages for {artist.name}: {total_pages} (Total items: {total})",
                    style="green",
                )

            # Respect optional max_pages cap
            if max_pages is not None and page >= max_pages:
                console.print(
                    f"⛔ Reached max_pages cap ({max_pages}); stopping", style="yellow"
                )
                break

            if page >= total_pages:
                console.print(
                    f"🏁 Reached last page ({page}/{total_pages}), stopping",
                    style="green",
                )
                break

            page += 1
            time.sleep(self.config.rate_limit_delay)

        console.print(
            f"🎉 {artist.name}: {len(all_shows)} new shows collected",
            style="bold green",
        )
        return all_shows

    def fetch_artist_setlists_window(
        self,
        artist: Artist,
        since_date: datetime,
        end_date: Optional[datetime] = None,
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch setlists within an explicit date window using the API's date range filter.

        This avoids scanning full history when only a recent window is needed.
        """
        all_shows: List[Dict[str, Any]] = []
        page = 1
        total_pages = None

        start_date = since_date.date()
        end_date_val = (
            end_date.date() if isinstance(end_date, datetime) else end_date
        ) or datetime.now().date()

        start_date_str = start_date.strftime("%d-%m-%Y")
        end_date_str = end_date_val.strftime("%d-%m-%Y")

        console.print(
            f"🎵 Fetching setlists for {artist.name} in window {start_date_str} to {end_date_str}",
            style="blue",
        )

        while True:
            url = self.config.get_artist_setlists_url(artist.musicbrainz_id, page)
            url += f"&date={start_date_str}-{end_date_str}"

            console.print(f"📄 Page {page}: {url}", style="cyan")

            try:
                response = self.make_api_request_with_retry(url)
            except requests.RequestException as e:
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
            setlist_items = data.get("setlist", [])
            if not setlist_items:
                console.print(
                    f"✅ No more setlists found on page {page}, completed",
                    style="green",
                )
                break

            all_shows.extend(setlist_items)
            console.print(
                f"✅ Fetched {len(setlist_items)} shows from page {page} (total so far: {len(all_shows)})",
                style="green",
            )

            if total_pages is None:
                items_per_page = int(data.get("itemsPerPage", 20))
                total = int(data.get("total", 0))
                total_pages = math.ceil(total / items_per_page) if items_per_page else 1
                console.print(
                    f"📊 Total pages (windowed) for {artist.name}: {total_pages} (Total items: {total})",
                    style="green",
                )

            if max_pages is not None and page >= max_pages:
                console.print(
                    f"⛔ Reached max_pages cap ({max_pages}); stopping", style="yellow"
                )
                break

            if page >= total_pages:
                console.print(
                    f"🏁 Reached last page ({page}/{total_pages}), stopping",
                    style="green",
                )
                break

            page += 1
            console.print(
                f"⏳ Waiting {self.config.rate_limit_delay} seconds before next request...",
                style="yellow",
            )
            time.sleep(self.config.rate_limit_delay)

        console.print(
            f"🎉 {artist.name}: {len(all_shows)} shows collected in window",
            style="bold green",
        )
        return all_shows

    def fetch_all_artists_historical(
        self, artists: Optional[List[Artist]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch historical setlists for all artists"""
        if artists is None:
            artists = self.artist_config.get_active_artists()

        all_artist_data = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Fetching historical data for all artists...", total=len(artists)
            )

            for artist in artists:
                progress.update(task, description=f"Fetching {artist.name}...")

                try:
                    shows = self.fetch_artist_setlists(artist, artist.starting_tour)
                    all_artist_data[artist.musicbrainz_id] = {
                        "artist": artist,
                        "shows": shows,
                    }
                except Exception as e:
                    console.print(
                        f"❌ Failed to fetch data for {artist.name}: {e}", style="red"
                    )
                    all_artist_data[artist.musicbrainz_id] = {
                        "artist": artist,
                        "shows": [],
                        "error": str(e),
                    }

                progress.advance(task)

        return all_artist_data

    def save_data_to_file(
        self, data: Dict[str, Any], filename: str, output_dir: Path = None
    ) -> Path:
        """Save API data to timestamped JSON file"""
        if output_dir is None:
            output_dir = Path("data/external")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Add metadata
        data_with_metadata = {
            "metadata": {
                "fetched_at": datetime.now().isoformat(),
                "api_version": "1.0",
                "total_artists": len(data),
                "total_shows": sum(
                    len(artist_data.get("shows", [])) for artist_data in data.values()
                ),
            },
            "data": data,
        }

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = output_dir / f"{filename}_{timestamp}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_with_metadata, f, indent=2, ensure_ascii=False)

        console.print(f"💾 Data saved to: {file_path}", style="green")
        return file_path


# Note: This file is a library (API client). Use scripts/ingest_setlistfm_to_snowflake.py to run end-to-end ingestion.
