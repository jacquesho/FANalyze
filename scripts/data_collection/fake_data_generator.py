# scripts/data_collection/fake_data_generator.py
import csv
import json
from dataclasses import dataclass, asdict
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from faker import Faker


@dataclass
class TicketSaleRecord:
    id: int
    data_content: str  # serialized JSON payload of the ticket sale
    file_name: str     # source file name for lineage


class FakeDataGenerator:
    def __init__(self):
        self.fake = Faker()
        self.data_dir = Path("data/external")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _generate_ticket_sale_payload(self, show_id: str, show_date: datetime) -> Dict:
        """Create a single fake ticket sale JSON payload."""
        section = self.fake.random_element(["GA", "VIP", "A", "B", "C", "Upper" ])
        row = self.fake.random_int(min=1, max=40)
        seat = self.fake.random_int(min=1, max=30)
        quantity = self.fake.random_int(min=1, max=4)
        price = round(self.fake.pyfloat(left_digits=2, right_digits=2, positive=True, min_value=25, max_value=350), 2)
        fee = round(price * 0.12, 2)
        total = round((price + fee) * quantity, 2)
        purchase_dt = show_date - timedelta(days=self.fake.random_int(min=5, max=120))

        return {
            "sale_id": self.fake.uuid4(),
            "show_id": show_id,
            "artist": self.fake.random_element([
                "Metallica", "Taylor Swift", "Beyoncé", "Coldplay", "Ed Sheeran"
            ]),
            "venue": self.fake.city() + " Arena",
            "city": self.fake.city(),
            "country": self.fake.country_code(),
            "section": section,
            "row": row,
            "seat": seat,
            "quantity": quantity,
            "unit_price": price,
            "service_fee": fee,
            "currency": "USD",
            "total_amount": total,
            "purchase_ts": purchase_dt.isoformat(),
            "show_date": show_date.date().isoformat(),
        }

    def generate_historical_ticket_sales(self, count: int = 500) -> List[TicketSaleRecord]:
        """Generate historical ticket sales mapped to ingestion schema (id, data_content, file_name)."""
        records: List[TicketSaleRecord] = []
        base_file_name = f"historical_ticket_sales_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        target_file = f"{base_file_name}.csv"

        for idx in range(1, count + 1):
            show_id = self.fake.uuid4()
            show_date = datetime.utcnow() - timedelta(days=self.fake.random_int(min=30, max=900))
            payload = self._generate_ticket_sale_payload(show_id, show_date)
            record = TicketSaleRecord(
                id=idx,
                data_content=json.dumps(payload, separators=(",", ":")),
                file_name=target_file,
            )
            records.append(record)

        return records

    def save_records_as_csv(self, records: List[TicketSaleRecord], filename: str) -> Path:
        """Save TicketSaleRecord list to CSV with columns id,data_content,file_name."""
        filepath = self.data_dir / f"{filename}.csv"
        with filepath.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "data_content", "file_name"])
            for rec in records:
                writer.writerow([rec.id, rec.data_content, rec.file_name])
        return filepath

    def save_records_as_jsonl(self, records: List[TicketSaleRecord], filename: str) -> Path:
        """Save TicketSaleRecord list to JSONL for optional downstream uses."""
        filepath = self.data_dir / f"{filename}.jsonl"
        with filepath.open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(asdict(rec)) + "\n")
        return filepath


def main():
    parser = argparse.ArgumentParser(description="Generate fake ticket sales data")
    parser.add_argument("--format", choices=["csv", "jsonl", "both"], default="jsonl", help="Output format")
    parser.add_argument("--count", type=int, default=500, help="Number of records to generate")
    parser.add_argument("--stream", action="store_true", help="Stream records (JSONL) one-by-one")
    parser.add_argument("--rate", type=float, default=1.0, help="Records per second when streaming")
    args = parser.parse_args()

    generator = FakeDataGenerator()
    base_name = f"ticket_sales_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    if args.stream:
        # Streaming mode writes JSONL and appends one record at a time
        filepath = generator.data_dir / f"{base_name}.jsonl"
        with filepath.open("w", encoding="utf-8") as f:
            for idx, rec in enumerate(generator.generate_historical_ticket_sales(count=args.count), start=1):
                f.write(json.dumps(asdict(rec)) + "\n")
                f.flush()
                print(f"⬇️ wrote record {idx} to {filepath}")
                if args.rate > 0:
                    time.sleep(1.0 / args.rate)
        print(f"✅ Streaming complete: {filepath}")
        return

    records = generator.generate_historical_ticket_sales(count=args.count)

    out_paths = []
    if args.format in ("csv", "both"):
        out_paths.append(generator.save_records_as_csv(records, base_name))
    if args.format in ("jsonl", "both"):
        out_paths.append(generator.save_records_as_jsonl(records, base_name))

    for p in out_paths:
        print(f"✅ Generated: {p}")


if __name__ == "__main__":
    main()