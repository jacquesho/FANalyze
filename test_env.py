import os
from dotenv import load_dotenv

load_dotenv()

print("KAFKA_BOOTSTRAP =", os.getenv("KAFKA_BOOTSTRAP"))
print("KAFKA_TOPIC =", os.getenv("KAFKA_TOPIC"))
print("KAFKA_API_KEY =", os.getenv("KAFKA_API_KEY"))
print("KAFKA_API_SECRET =", os.getenv("KAFKA_API_SECRET"))
