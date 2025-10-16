#!/usr/bin/env python3
"""
API Configuration for FANalyze v2.0
Contains API endpoints, rate limiting, and connection settings
"""

import os
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class APIConfig:
    """Base API configuration"""
    base_url: str
    api_key: str
    headers: Dict[str, str]
    rate_limit_delay: float = 1.1  # seconds between requests
    max_retries: int = 3
    timeout: int = 10


class SetlistFMConfig(APIConfig):
    """SetlistFM API configuration"""
    
    def __init__(self):
        super().__init__(
            base_url="https://api.setlist.fm/rest/1.0",
            api_key=os.getenv("SETLISTFM_API_KEY"),
            headers={
                "x-api-key": os.getenv("SETLISTFM_API_KEY"),
                "Accept": "application/json",
                "User-Agent": "FANalyze/2.0 (jacquesho@gmail.com)"
            },
            rate_limit_delay=1.1,  # SetlistFM rate limit
            max_retries=3,
            timeout=10
        )
    
    def get_artist_setlists_url(self, artist_id: str, page: int = 1) -> str:
        """Get URL for artist setlists endpoint"""
        return f"{self.base_url}/artist/{artist_id}/setlists?p={page}"
    
    def get_setlist_details_url(self, setlist_id: str) -> str:
        """Get URL for setlist details endpoint"""
        return f"{self.base_url}/setlist/{setlist_id}"
    
    def get_artist_url(self, artist_id: str) -> str:
        """Get URL for artist details endpoint"""
        return f"{self.base_url}/artist/{artist_id}"

    # Note: City filtering via /search/setlists was removed per request to fetch full history.


class APIConfigManager:
    """Manages all API configurations"""
    
    def __init__(self):
        self.setlistfm = SetlistFMConfig()
    
    def validate_configs(self) -> Dict[str, bool]:
        """Validate that all required API keys are present"""
        validation_results = {}
        
        # Check SetlistFM API key
        validation_results["setlistfm"] = bool(self.setlistfm.api_key)
        
        return validation_results
    
    def print_config_status(self) -> None:
        """Print configuration status"""
        print("🔧 API Configuration Status")
        print("=" * 40)
        
        validation = self.validate_configs()
        
        for api_name, is_valid in validation.items():
            status = "✅ Valid" if is_valid else "❌ Missing API Key"
            print(f"{api_name.upper()}: {status}")
        
        print()
        
        if all(validation.values()):
            print("🚀 All API configurations are ready!")
        else:
            print("⚠️  Some API keys are missing. Check your .env file.")


# Global instance
api_config = APIConfigManager()


def main():
    """Main function to demonstrate API configuration"""
    config = APIConfigManager()
    config.print_config_status()
    
    # Example URLs
    if config.setlistfm.api_key:
        print("🔗 Example SetlistFM URLs:")
        print(f"Artist Setlists: {config.setlistfm.get_artist_setlists_url('65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab')}")
        print(f"Setlist Details: {config.setlistfm.get_setlist_details_url('example-setlist-id')}")


if __name__ == "__main__":
    main()
