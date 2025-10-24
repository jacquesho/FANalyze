#!/usr/bin/env python3
"""
API Configuration for FANalyze v2.0
Contains API endpoints, rate limiting, and connection settings
"""

import os
import snowflake.connector
from cryptography.hazmat.primitives import serialization
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


def get_snowflake_connection():
    """Get Snowflake connection using keypair authentication"""
    try:
        # Get keypair file path
        keypair_path = os.getenv('SNOWFLAKE_KEYPAIR_PATH', '.secrets/rsa_key.p8')
        private_key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), keypair_path)
        
        # Read and convert private key from PKCS#8 to PEM format
        with open(private_key_path, 'rb') as key_file:
            private_key_pem = key_file.read()
        
        # Load the private key and convert to DER format for Snowflake
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,  # No password for unencrypted keys
        )
        
        # Convert to DER format
        private_key_der = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA', 'FAN_RAW'),
            role=os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN'),
            private_key=private_key_der,
            authenticator='snowflake'
        )
        return conn
    except Exception as e:
        raise Exception(f"Failed to connect to Snowflake: {e}")


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
