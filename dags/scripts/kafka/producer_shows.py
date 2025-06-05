import argparse
from kafka import KafkaProducer
import json
import os

# Define your Kafka topics
TOPIC_MAP = {
    "historical": "historical_shows_topic",
    "scheduled": "scheduled_shows_topic",
}


def load_show_data(mode):
    from pathlib import Path
    import json

    data_dir = Path("/opt/airflow/models/01_staging/setlistfm_data")
    matched_files = list(data_dir.glob("*.json"))

    if not matched_files:
        raise FileNotFoundError(f"No JSON files found in {data_dir}")

    file_path = matched_files[0]

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def produce_messages(mode):
    if mode not in TOPIC_MAP:
        raise ValueError(
            f"Unsupported mode: {mode}. Choose from {list(TOPIC_MAP.keys())}"
        )

    topic = TOPIC_MAP[mode]
    try:
        producer = KafkaProducer(
            bootstrap_servers=["kafka:9092"],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            api_version=(0, 10, 1),  # Added explicit API version
            request_timeout_ms=5000,  # Added timeout
        )
        print("✅ Successfully connected to Kafka")
    except Exception as e:
        print(f"❌ Failed to connect to Kafka: {str(e)}")
        raise

    events = load_show_data(mode)

    for event in events:
        producer.send(topic, value=event)
        print(f"✅ Sent to {topic}: {event}")

    producer.flush()
    producer.close()
    print("🟢 Producer closed.")


def main():
    parser = argparse.ArgumentParser(description="Produce show data to Kafka.")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["historical", "scheduled"],
        help="Which mode of data to send: 'historical' or 'scheduled'",
    )
    args = parser.parse_args()
    produce_messages(args.mode)


if __name__ == "__main__":
    main()
