#!/usr/bin/env python3
"""
API Configuration for FANalyze v2.0
Contains API endpoints, rate limiting, and connection settings
"""

import os
import snowflake.connector
from cryptography.hazmat.primitives import serialization
from dataclasses import dataclass
from typing import Dict
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
                "User-Agent": "FANalyze/2.0 (jacquesho@gmail.com)",
            },
            rate_limit_delay=1.1,  # SetlistFM rate limit
            max_retries=3,
            timeout=10,
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
        # Get keypair file path - handle both absolute and relative paths
        keypair_path = os.getenv("SNOWFLAKE_KEYPAIR_PATH", ".secrets/rsa_key.p8")

        # If path is absolute, use it directly; otherwise construct relative to project root
        if os.path.isabs(keypair_path):
            private_key_path = keypair_path
        else:
            # Try to get project root - check if we're in Airflow container first
            if os.path.exists("/opt/airflow/.secrets"):
                # Running in Airflow container
                # Remove leading "./" but preserve ".secrets" directory name
                normalized_path = (
                    keypair_path.lstrip("./")
                    if keypair_path.startswith("./")
                    else keypair_path
                )
                # If normalized path doesn't start with .secrets, it was stripped - restore it
                if keypair_path.startswith(
                    ".secrets"
                ) and not normalized_path.startswith(".secrets"):
                    normalized_path = ".secrets/" + normalized_path
                private_key_path = os.path.join("/opt/airflow", normalized_path)
            elif __file__:
                # Running locally - go up from config/ directory to project root
                project_root = os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
                private_key_path = os.path.join(project_root, keypair_path)
            else:
                # Fallback: try current working directory
                private_key_path = os.path.join(os.getcwd(), keypair_path)

        # Validate required environment variables
        required_vars = [
            "SNOWFLAKE_USER",
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_WAREHOUSE",
            "SNOWFLAKE_DATABASE",
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise Exception(
                f"Missing required Snowflake environment variables: {', '.join(missing_vars)}"
            )

        # Read and convert private key from PKCS#8 to PEM format
        if not os.path.exists(private_key_path):
            raise Exception(
                f"Snowflake private key file not found at: {private_key_path}"
            )

        with open(private_key_path, "rb") as key_file:
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
            encryption_algorithm=serialization.NoEncryption(),
        )

        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA", "FAN_RAW"),
            role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
            private_key=private_key_der,
            authenticator="snowflake",
            login_timeout=60,  # 60 seconds timeout for login
            network_timeout=60,  # 60 seconds timeout for network operations
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
        print(
            f"Artist Setlists: {config.setlistfm.get_artist_setlists_url('65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab')}"
        )
        print(
            f"Setlist Details: {config.setlistfm.get_setlist_details_url('example-setlist-id')}"
        )


if __name__ == "__main__":
    main()
