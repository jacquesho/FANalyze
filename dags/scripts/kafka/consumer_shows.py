import argparse
import json
import os
from kafka import KafkaConsumer
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

# Map mode to topic name
TOPIC_MAP = {
    "historical": "historical_shows_topic",
    "scheduled": "scheduled_shows_topic"
}

def get_snowflake_connection():
    hook = SnowflakeHook(snowflake_conn_id="fanalyze_conn")
    return hook.get_conn()

def insert_event_to_snowflake(conn, event):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO FANALYZE.KAFKA_SHOWS_LOAD (show_id, artist, raw_event)
            VALUES (%s, %s, PARSE_JSON(%s))
        """, (
            event.get("show_id"),
            event.get("artist"),
            json.dumps(event)
        ))
        conn.commit()
    finally:
        cursor.close()

def consume_messages(mode):
    if mode not in TOPIC_MAP:
        raise ValueError(f"Invalid mode: {mode}. Choose from {list(TOPIC_MAP.keys())}")

    topic = TOPIC_MAP[mode]
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    conn = get_snowflake_connection()
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id=f"{mode}_consumer_group"
    )

    print(f"🔄 Listening to topic: {topic} (mode: {mode})")

    try:
        for message in consumer:
            event = message.value
            print(f"📥 Message received: {event}")
            insert_event_to_snowflake(conn, event)
            print("✅ Inserted into KAFKA_SHOWS_LOAD")
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        consumer.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Kafka consumer for show data to Snowflake")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["historical", "scheduled"],
        help="Which mode of topic to consume: 'historical' or 'scheduled'"
    )
    args = parser.parse_args()
    consume_messages(args.mode)

if __name__ == "__main__":
    main()
