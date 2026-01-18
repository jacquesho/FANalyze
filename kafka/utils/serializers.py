"""
Serialization utilities for Kafka messages
Handles conversion between Python objects and bytes for Kafka
"""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def serialize_json(data: Dict[str, Any]) -> bytes:
    """
    Serialize Python dict to JSON bytes for Kafka.

    Args:
        data: Python dictionary to serialize

    Returns:
        bytes: JSON-encoded bytes ready for Kafka

    Raises:
        TypeError: If data cannot be serialized to JSON
    """
    try:
        json_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        return json_str.encode("utf-8")
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize data to JSON: {e}")
        raise


def deserialize_json(data: bytes) -> Dict[str, Any]:
    """
    Deserialize JSON bytes from Kafka to Python dict.

    Args:
        data: Bytes received from Kafka

    Returns:
        dict: Deserialized Python dictionary

    Raises:
        json.JSONDecodeError: If data is not valid JSON
    """
    try:
        json_str = data.decode("utf-8")
        return json.loads(json_str)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.error(f"Failed to deserialize JSON data: {e}")
        raise
