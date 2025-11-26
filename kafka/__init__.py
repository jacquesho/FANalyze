"""
Kafka infrastructure for FANalyze v2.0
Provides base producer/consumer classes and business logic implementations
"""

from kafka.base_producer import BaseProducer
from kafka.base_consumer import BaseConsumer

__all__ = ['BaseProducer', 'BaseConsumer']
