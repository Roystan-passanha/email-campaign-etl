"""Load: write clean tables to SQLite and build the reporting view."""
import sqlite3
from pathlib import Path

import pandas as pd

VIEW = """
CREATE VIEW campaign_kpis AS
WITH delivered AS (
    SELECT campaign_id, COUNT(*) AS sent,
           SUM(delivery_status = 'Delivered') AS delivered
    FROM sends GROUP BY campaign_id
),
ev AS (
    SELECT campaign_id,
           SUM(event_type = 'open')        AS unique_opens,
           SUM(event_type = 'click')       AS unique_clicks,
           SUM(event_type = 'unsubscribe') AS unsubscribes
    FROM events GROUP BY campaign_id
)
SELECT c.campaign_id, c.campaign_name, c.campaign_type, date(c.send_time) AS send_date,
       d.sent, d.delivered,
       ROUND(100.0 * d.delivered / d.sent, 1)           AS delivery_rate,
       ROUND(100.0 * e.unique_opens / d.delivered, 1)   AS open_rate,
       ROUND(100.0 * e.unique_clicks / d.delivered, 1)  AS click_rate,
       ROUND(100.0 * e.unique_clicks / e.unique_opens, 1) AS click_to_open_rate,
       ROUND(100.0 * e.unsubscribes / d.delivered, 2)   AS unsubscribe_rate
FROM campaigns c
JOIN delivered d USING (campaign_id)
JOIN ev e USING (campaign_id)
ORDER BY c.send_time;
"""


def load(tables: dict[str, pd.DataFrame], db_path: Path) -> sqlite3.Connection:
    db_path.unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    for name, df in tables.items():
        df.to_sql(name, con, index=False)
    con.execute("CREATE INDEX ix_events ON events (campaign_id, event_type)")
    con.executescript(VIEW)
    con.commit()
    return con
