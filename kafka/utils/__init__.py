"""
Kafka utility functions
"""

from kafka.utils.serializers import serialize_json, deserialize_json

__all__ = ['serialize_json', 'deserialize_json']
