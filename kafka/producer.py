import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from kafka import KafkaProducer

# Load environment variables from root-level .env
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP")
API_KEY = os.getenv("KAFKA_API_KEY")
API_SECRET = os.getenv("KAFKA_API_SECRET")
SEC_PROTO = "SASL_SSL" if API_KEY else "PLAINTEXT"

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP,
    security_protocol=SEC_PROTO,
    sasl_mechanism="PLAIN" if API_KEY else None,
    sasl_plain_username=API_KEY,
    sasl_plain_password=API_SECRET,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

for i in range(5):
    event = {"event_id": i, "ts": time.time(), "artist": "Metallica"}
    producer.send("concert_events", event)
    print("Sent", event)
    time.sleep(1)

producer.flush()
print("✅ All events sent")
