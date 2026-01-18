"""
Base Kafka Producer
Infrastructure layer: handles Kafka client, retry logic, error handling, logging
"""

import os
import logging
from typing import Optional, Dict
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
)
logger = logging.getLogger(__name__)


class BaseProducer:
    """
    Base Kafka producer with infrastructure concerns:
    - Client configuration
    - Message sending with retry logic
    - Topic creation
    - Error handling
    - Logging
    """

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        client_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize base producer.

        Args:
            bootstrap_servers: Kafka broker addresses (defaults to env var)
            client_id: Client identifier (defaults to class name)
            **kwargs: Additional producer configuration
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:29092"
        )
        self.client_id = client_id or self.__class__.__name__

        # Producer configuration with sensible defaults
        producer_config = {
            "bootstrap.servers": self.bootstrap_servers,
            "client.id": self.client_id,
            "acks": "all",  # Wait for all replicas (most reliable)
            "retries": 3,  # Retry failed sends
            "max.in.flight.requests.per.connection": 1,  # Prevent reordering
            **kwargs,  # Allow override of defaults
        }

        self.producer = Producer(producer_config)
        logger.info(
            f"Initialized {self.client_id} producer "
            f"connecting to {self.bootstrap_servers}"
        )

    def create_topic_if_not_exists(
        self, topic_name: str, num_partitions: int = 3, replication_factor: int = 1
    ) -> bool:
        """
        Create Kafka topic if it doesn't exist.

        Args:
            topic_name: Name of the topic to create
            num_partitions: Number of partitions (default: 3)
            replication_factor: Replication factor (default: 1 for single node)

        Returns:
            bool: True if topic exists or was created successfully
        """
        try:
            admin_client = AdminClient({"bootstrap.servers": self.bootstrap_servers})

            # Check if topic already exists
            metadata = admin_client.list_topics(timeout=10)
            if topic_name in metadata.topics:
                logger.info(f"Topic '{topic_name}' already exists")
                return True

            # Create new topic
            new_topic = NewTopic(
                topic=topic_name,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
            )

            fs = admin_client.create_topics([new_topic])

            # Wait for topic creation to complete
            for topic, f in fs.items():
                try:
                    f.result()  # The result itself is None
                    logger.info(
                        f"✅ Topic '{topic}' created successfully "
                        f"({num_partitions} partitions, replication={replication_factor})"
                    )
                    return True
                except Exception as e:
                    logger.error(f"❌ Failed to create topic '{topic}': {e}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error creating topic: {e}")
            return False

    def send(
        self,
        topic: str,
        key: Optional[str],
        value: bytes,
        headers: Optional[Dict[str, str]] = None,
        callback: Optional[callable] = None,
    ) -> None:
        """
        Send message to Kafka topic with automatic retry.

        Args:
            topic: Topic name
            key: Message key (used for partitioning)
            value: Message value (bytes)
            headers: Optional message headers
            callback: Optional delivery callback function
        """
        try:
            self.producer.produce(
                topic=topic,
                key=key.encode("utf-8") if key else None,
                value=value,
                headers=headers,
                callback=callback or self._default_delivery_callback,
            )
            # Trigger delivery reports (non-blocking)
            self.producer.poll(0)
        except Exception as e:
            logger.error(f"❌ Failed to send message to topic '{topic}': {e}")
            raise

    def _default_delivery_callback(self, err, msg):
        """Default callback for message delivery confirmation"""
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(
                f"Message delivered to {msg.topic()}[{msg.partition()}] "
                f"@ offset {msg.offset()}"
            )

    def flush(self, timeout: float = 10.0) -> None:
        """
        Wait for all messages to be delivered.

        Args:
            timeout: Maximum time to wait in seconds
        """
        try:
            remaining = self.producer.flush(timeout)
            if remaining > 0:
                logger.warning(f"{remaining} messages were not delivered")
            else:
                logger.debug("All messages delivered successfully")
        except Exception as e:
            logger.error(f"Error flushing producer: {e}")
            raise

    def close(self) -> None:
        """Clean shutdown of producer"""
        try:
            self.flush()
            logger.info(f"{self.client_id} producer closed")
        except Exception as e:
            logger.error(f"Error closing producer: {e}")
