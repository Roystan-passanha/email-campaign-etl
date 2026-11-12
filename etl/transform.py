"""Transform: clean, deduplicate and remove machine clicks."""
import pandas as pd

DATE_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%m-%d-%Y %I:%M %p"]
BOT_CLICK_SECONDS = 10  # clicks this soon after sending are link scanners, not people


def parse_datetime(series: pd.Series) -> pd.Series:
    """Try each known export format; anything left unparsed stays NaT and is reported."""
    out = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    for fmt in DATE_FORMATS:
        missing = out.isna()
        if not missing.any():
            break
        out[missing] = pd.to_datetime(series[missing], format=fmt, errors="coerce")
    return out


def normalise_email(series: pd.Series) -> pd.Series:
    return series.str.strip().str.lower()


def transform(raw: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], dict[str, int]]:
    stats: dict[str, int] = {}
    campaigns = raw["campaigns"].copy()
    campaigns["send_time"] = parse_datetime(campaigns["send_time"])

    sends = raw["sends"].copy()
    sends["email"] = normalise_email(sends["email"])
    sends["sent_at"] = parse_datetime(sends["sent_at"])
    before = len(sends)
    sends = sends.drop_duplicates(["campaign_id", "email"])
    stats["duplicate_sends_removed"] = before - len(sends)

    events = raw["events"].copy()
    events["email"] = normalise_email(events["email"])
    events["event_type"] = events["event_type"].str.strip().str.lower()
    events["event_time"] = parse_datetime(events["event_time"])
    stats["unparsed_event_dates"] = int(events["event_time"].isna().sum())
    events = events.dropna(subset=["event_time"])

    # machine clicks: compare with the campaign send time
    events = events.merge(campaigns[["campaign_id", "send_time"]], on="campaign_id", how="left")
    seconds = (events["event_time"] - events["send_time"]).dt.total_seconds()
    bot = (events["event_type"] == "click") & (seconds < BOT_CLICK_SECONDS)
    stats["bot_clicks_removed"] = int(bot.sum())
    events = events[~bot].drop(columns="send_time")

    # keep first event of each type per person per campaign
    before = len(events)
    events = events.sort_values("event_time").drop_duplicates(["campaign_id", "email", "event_type"])
    stats["duplicate_events_removed"] = before - len(events)

    return {"campaigns": campaigns, "sends": sends, "events": events}, stats
