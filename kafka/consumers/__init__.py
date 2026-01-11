"""
Kafka consumers for FANalyze v2.0
Business logic implementations for consuming messages from Kafka
"""

from kafka.consumers.postgres_consumer import PostgresConsumer

__all__ = ["PostgresConsumer"]
