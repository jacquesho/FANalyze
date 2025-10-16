#!/usr/bin/env python3
"""
Artist Configuration for FANalyze v2.0
Contains artist metadata including MusicBrainz IDs for API calls
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import json
from pathlib import Path


@dataclass
class Artist:
    """Artist configuration data class"""
    name: str
    musicbrainz_id: str
    genre: str
    active: bool = True
    starting_tour: Optional[str] = None
    notes: Optional[str] = None


class ArtistConfig:
    """Artist configuration manager"""
    
    def __init__(self):
        self.artists = self._load_artists()
    
    def _load_artists(self) -> List[Artist]:
        """Load artist configurations"""
        return [
            # Core artist from v1.0
            Artist(
                name="Metallica",
                musicbrainz_id="65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab",
                genre="Heavy Metal, Thrash Metal, Speed Metal, Hard Rock",
                active=True,
                notes="Primary artist from v1.0"
            ),
            
            # New artists for v2.0 - POPULAR MUSIC FOCUS
            Artist(
                name="Taylor Swift",
                musicbrainz_id="20244d07-534f-4eff-b4d4-930878889970",
                genre="Pop, Country Pop, Synth-pop, Alternative Pop",
                active=False,
                notes="Global pop superstar with extensive touring history"
            ),
            Artist(
                name="Coldplay",
                musicbrainz_id="cc197bad-dc9c-440d-a5b5-d52ba2e14234",
                genre="Alternative Rock, Pop Rock, Post-Britpop",
                active=False,
                notes="British rock band known for stadium tours"
            ),
            Artist(
                name="Beyoncé",
                musicbrainz_id="859d0860-d480-4efd-970c-c05d5f1776b8",
                genre="R&B, Pop, Hip Hop, Soul",
                active=False,
                notes="Global R&B and pop icon"
            ),
            Artist(
                name="Ed Sheeran",
                musicbrainz_id="b8a7c51f-362c-4dcb-a259-bc6e0095f0a6",
                genre="Pop, Folk Pop, Acoustic Pop",
                active=False,
                notes="British singer-songwriter with acoustic pop style"
            ),
            Artist(
                name="The Weeknd",
                musicbrainz_id="c8b03190-306c-4120-bb0b-6f2ebfc06ea9",
                genre="R&B, Pop, Alternative R&B, Synth-pop",
                active=False,
                notes="Canadian R&B and pop artist"
            ),
            Artist(
                name="Bruno Mars",
                musicbrainz_id="afb680f2-b6eb-4cd7-a70b-a63b25c763d5",
                genre="Pop, Funk, R&B, Rock, Soul",
                active=False,
                notes="American singer-songwriter"
            )
        ]
    
    def get_active_artists(self) -> List[Artist]:
        """Get all active artists"""
        return [artist for artist in self.artists if artist.active]
    
    def get_artist_by_id(self, musicbrainz_id: str) -> Optional[Artist]:
        """Get artist by MusicBrainz ID"""
        for artist in self.artists:
            if artist.musicbrainz_id == musicbrainz_id:
                return artist
        return None
    
    def get_artist_by_name(self, name: str) -> Optional[Artist]:
        """Get artist by name (case-insensitive)"""
        for artist in self.artists:
            if artist.name.lower() == name.lower():
                return artist
        return None
    
    def get_artists_for_api(self) -> List[Dict[str, str]]:
        """Get artists formatted for API calls"""
        return [
            {
                "artist_id": artist.musicbrainz_id,
                "artist_name": artist.name,
                "genre": artist.genre,
                "starting_tour": artist.starting_tour
            }
            for artist in self.get_active_artists()
        ]
    
    def export_to_json(self, file_path: Path) -> None:
        """Export artist configuration to JSON file"""
        artists_data = [
            {
                "name": artist.name,
                "musicbrainz_id": artist.musicbrainz_id,
                "genre": artist.genre,
                "active": artist.active,
                "starting_tour": artist.starting_tour,
                "notes": artist.notes
            }
            for artist in self.artists
        ]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(artists_data, f, indent=2)
    
    def import_from_json(self, file_path: Path) -> None:
        """Import artist configuration from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            artists_data = json.load(f)
        
        self.artists = [
            Artist(
                name=artist["name"],
                musicbrainz_id=artist["musicbrainz_id"],
                genre=artist["genre"],
                active=artist.get("active", True),
                starting_tour=artist.get("starting_tour"),
                notes=artist.get("notes")
            )
            for artist in artists_data
        ]
    
    def print_summary(self) -> None:
        """Print a summary of all artists"""
        print("🎵 FANalyze v2.0 Artist Configuration")
        print("=" * 50)
        print(f"Total Artists: {len(self.artists)}")
        print(f"Active Artists: {len(self.get_active_artists())}")
        print()
        
        for i, artist in enumerate(self.get_active_artists(), 1):
            print(f"{i}. {artist.name}")
            print(f"   MusicBrainz ID: {artist.musicbrainz_id}")
            print(f"   Genre: {artist.genre}")
            if artist.starting_tour:
                print(f"   Starting Tour: {artist.starting_tour}")
            if artist.notes:
                print(f"   Notes: {artist.notes}")
            print()


# Global instance
artist_config = ArtistConfig()


def main():
    """Main function to demonstrate artist configuration"""
    config = ArtistConfig()
    config.print_summary()
    
    # Example usage
    print("\n🔍 Example API calls:")
    for artist_data in config.get_artists_for_api()[:3]:  # Show first 3
        print(f"Artist: {artist_data['artist_name']}")
        print(f"API URL: https://api.setlist.fm/rest/1.0/artist/{artist_data['artist_id']}/setlists")
        print()


if __name__ == "__main__":
    main()
