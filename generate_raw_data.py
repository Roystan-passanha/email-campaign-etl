"""Create messy, synthetic email platform exports in raw/ for the pipeline to clean.

Mimics what marketing tools export: inconsistent date formats, upper/lower case
emails with spaces, duplicate events, and machine (bot) clicks that fire within
seconds of delivery. All data is invented.
"""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(11)
RAW = Path(__file__).resolve().parent / "raw"

CAMPAIGNS = [
    ("CMP-01", "Spring welcome", "Promotional", "2025-03-04 09:00"),
    ("CMP-02", "Product update", "Newsletter", "2025-03-11 10:00"),
    ("CMP-03", "Spring sale", "Promotional", "2025-03-18 09:00"),
    ("CMP-04", "Customer survey", "Engagement", "2025-03-25 11:00"),
    ("CMP-05", "April newsletter", "Newsletter", "2025-04-01 10:00"),
    ("CMP-06", "Win-back offer", "Promotional", "2025-04-08 09:00"),
]
# open rate, click rate given open, unsubscribe rate
PROFILE = {
    "CMP-01": (0.42, 0.18, 0.004), "CMP-02": (0.31, 0.09, 0.002), "CMP-03": (0.38, 0.22, 0.006),
    "CMP-04": (0.27, 0.12, 0.003), "CMP-05": (0.29, 0.08, 0.002), "CMP-06": (0.22, 0.15, 0.011),
}
DATE_STYLES = ["%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M", "%m-%d-%Y %I:%M %p"]


def messy_email(n: int) -> str:
    email = f"subscriber{n:05d}@example.com"
    r = random.random()
    if r < 0.1:
        return email.upper()
    if r < 0.15:
        return f"  {email} "
    return email


def stamp(dt: datetime) -> str:
    return dt.strftime(random.choice(DATE_STYLES))


def main() -> None:
    RAW.mkdir(exist_ok=True)
    with (RAW / "campaigns.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Campaign ID", "Campaign Name", "Type", "Send Time"])
        w.writerows(CAMPAIGNS)

    sends, events = [], []
    for cid, _name, _type, send_time in CAMPAIGNS:
        sent = datetime.strptime(send_time, "%Y-%m-%d %H:%M")
        audience = random.sample(range(1, 12001), random.randint(7000, 9000))
        p_open, p_click, p_unsub = PROFILE[cid]
        for n in audience:
            email = messy_email(n)
            bounced = random.random() < 0.015
            sends.append([cid, email, stamp(sent), "Bounced" if bounced else "Delivered"])
            if bounced:
                continue
            if random.random() < 0.03:  # security scanner clicks within seconds
                events.append([cid, email, "click", stamp(sent + timedelta(seconds=random.randint(1, 8)))])
            if random.random() < p_open:
                t_open = sent + timedelta(minutes=random.randint(5, 2880))
                events.append([cid, email, "open", stamp(t_open)])
                if random.random() < 0.2:  # duplicate open
                    events.append([cid, email, "open", stamp(t_open + timedelta(minutes=random.randint(1, 600)))])
                if random.random() < p_click:
                    events.append([cid, email, "click", stamp(t_open + timedelta(seconds=random.randint(20, 900)))])
            if random.random() < p_unsub:
                events.append([cid, email, "unsubscribe", stamp(sent + timedelta(hours=random.randint(1, 72)))])

    random.shuffle(events)
    with (RAW / "sends.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["campaign_id", "Email Address", "Sent At", "Delivery Status"])
        w.writerows(sends)
    with (RAW / "events.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["CampaignID", "email", "event_type", "event_time"])
        w.writerows(events)
    print(f"Wrote {len(sends)} sends and {len(events)} events to {RAW}")


if __name__ == "__main__":
    main()
