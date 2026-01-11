"""
Base Kafka Consumer
Infrastructure layer: handles Kafka client, polling, offset management, error handling, logging
"""

import os
import logging
from typing import List, Optional
from confluent_kafka import Consumer, KafkaError, Message
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
)
logger = logging.getLogger(__name__)


class BaseConsumer:
    """
    Base Kafka consumer with infrastructure concerns:
    - Client configuration
    - Message polling with error handling
    - Offset management
    - Error handling
    - Logging
    """

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        group_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize base consumer.

        Args:
            bootstrap_servers: Kafka broker addresses (defaults to env var)
            group_id: Consumer group ID (defaults to env var or class name)
            **kwargs: Additional consumer configuration
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:29092"
        )
        self.group_id = group_id or os.getenv(
            "KAFKA_GROUP_ID", f"{self.__class__.__name__}-group"
        )

        # Consumer configuration with sensible defaults
        consumer_config = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "auto.offset.reset": "earliest",  # Start from beginning if no offset
            "enable.auto.commit": False,  # Manual commit for reliability
            **kwargs,  # Allow override of defaults
        }

        self.consumer = Consumer(consumer_config)
        logger.info(
            f"Initialized {self.__class__.__name__} consumer "
            f"(group: {self.group_id}) connecting to {self.bootstrap_servers}"
        )

    def subscribe(self, topics: List[str]) -> None:
        """
        Subscribe to Kafka topics.

        Args:
            topics: List of topic names to subscribe to
        """
        try:
            self.consumer.subscribe(topics)
            logger.info(f"✅ Subscribed to topics: {', '.join(topics)}")
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to topics: {e}")
            raise

    def poll(self, timeout: float = 1.0) -> Optional[Message]:
        """
        Poll for messages with error handling.

        Args:
            timeout: Maximum time to wait for a message in seconds

        Returns:
            Message object if message received, None if timeout
        """
        try:
            msg = self.consumer.poll(timeout)

            if msg is None:
                return None

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition - not an error, just no more messages
                    logger.debug(
                        f"Reached end of partition {msg.partition()} "
                        f"for topic {msg.topic()}"
                    )
                    return None
                else:
                    logger.error(f"Kafka error: {msg.error()}")
                    return None

            return msg

        except Exception as e:
            logger.error(f"Error polling for messages: {e}")
            return None

    def commit(
        self, message: Optional[Message] = None, asynchronous: bool = False
    ) -> None:
        """
        Commit offsets to Kafka.

        Args:
            message: Optional message to commit offset for (commits this message's offset)
            asynchronous: If True, commit asynchronously (faster but less reliable)
        """
        try:
            if message:
                # Commit specific message offset
                self.consumer.commit(message, asynchronous=asynchronous)
                logger.debug(
                    f"Committed offset for {message.topic()}[{message.partition()}] "
                    f"@ offset {message.offset()}"
                )
            else:
                # Commit all current offsets
                self.consumer.commit(asynchronous=asynchronous)
                logger.debug("Committed all offsets")
        except Exception as e:
            logger.error(f"Error committing offsets: {e}")
            raise

    def close(self) -> None:
        """Clean shutdown of consumer"""
        try:
            # Commit final offsets before closing
            self.commit()
            self.consumer.close()
            logger.info(f"{self.__class__.__name__} consumer closed")
        except Exception as e:
            logger.error(f"Error closing consumer: {e}")
