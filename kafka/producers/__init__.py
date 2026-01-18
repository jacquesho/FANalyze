"""
Kafka producers for FANalyze v2.0
Business logic implementations for producing messages to Kafka
"""

from kafka.producers.ticket_producer import TicketProducer

__all__ = ["TicketProducer"]
