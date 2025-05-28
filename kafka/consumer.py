import json
import os
from pathlib import Path
from dotenv import load_dotenv
from kafka import KafkaConsumer

# Load environment variables from root-level .env
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP")
API_KEY = os.getenv("KAFKA_API_KEY")
API_SECRET = os.getenv("KAFKA_API_SECRET")
SEC_PROTO = "SASL_SSL" if API_KEY else "PLAINTEXT"

consumer = KafkaConsumer(
    "concert_events",
    bootstrap_servers=BOOTSTRAP,
    security_protocol=SEC_PROTO,
    sasl_mechanism="PLAIN" if API_KEY else None,
    sasl_plain_username=API_KEY,
    sasl_plain_password=API_SECRET,
    auto_offset_reset="earliest",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
)

print("⏳ Waiting for messages…")
for msg in consumer:
    print("Received", msg.value)
