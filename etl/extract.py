"""Extract: read raw exports and rename columns to one standard."""
from pathlib import Path

import pandas as pd

COLUMN_MAP = {
    "campaign id": "campaign_id", "campaignid": "campaign_id", "campaign_id": "campaign_id",
    "campaign name": "campaign_name", "type": "campaign_type", "send time": "send_time",
    "email address": "email", "email": "email",
    "sent at": "sent_at", "delivery status": "delivery_status",
    "event_type": "event_type", "event_time": "event_time",
}


def read(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    df.columns = [COLUMN_MAP.get(c.strip().lower(), c.strip().lower()) for c in df.columns]
    return df


def extract(raw_dir: Path) -> dict[str, pd.DataFrame]:
    return {name: read(raw_dir / f"{name}.csv") for name in ("campaigns", "sends", "events")}
