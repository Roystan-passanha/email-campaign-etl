import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from etl.transform import normalise_email, parse_datetime, transform  # noqa: E402


def test_parse_datetime_reads_every_export_format():
    s = pd.Series(["2025-03-04 09:05:00", "04/03/2025 09:05", "03-04-2025 09:05 AM"])
    assert parse_datetime(s).nunique() == 1


def test_normalise_email():
    assert normalise_email(pd.Series(["  A@Example.COM "]))[0] == "a@example.com"


def make_raw():
    campaigns = pd.DataFrame({"campaign_id": ["C1"], "campaign_name": ["Test"],
                              "campaign_type": ["Promotional"], "send_time": ["2025-03-04 09:00"]})
    sends = pd.DataFrame({"campaign_id": ["C1", "C1"], "email": ["a@x.com", " A@X.COM"],
                          "sent_at": ["2025-03-04 09:00:00"] * 2, "delivery_status": ["Delivered"] * 2})
    events = pd.DataFrame({
        "campaign_id": ["C1"] * 4,
        "email": ["a@x.com", "A@X.com", "a@x.com", "a@x.com"],
        "event_type": ["open", "open", "click", "click"],
        "event_time": ["2025-03-04 10:00:00", "2025-03-04 11:00:00",
                       "2025-03-04 09:00:03",            # scanner click, 3 seconds after send
                       "2025-03-04 10:01:00"],
    })
    return {"campaigns": campaigns, "sends": sends, "events": events}


def test_transform_dedupes_and_removes_bot_clicks():
    tables, stats = transform(make_raw())
    assert len(tables["sends"]) == 1
    assert stats["bot_clicks_removed"] == 1
    assert stats["duplicate_events_removed"] == 1
    assert sorted(tables["events"]["event_type"]) == ["click", "open"]
