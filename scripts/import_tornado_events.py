"""
Import NOAA NCEI Storm Events CSV files into the tornado_events.events table.

Data source: https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/
Download StormEvents_details-ftp_v1.0_dYYYY_*.csv.gz files and pass them as arguments.

Usage:
    python import_tornado_events.py StormEvents_details*.csv.gz
    python import_tornado_events.py --host 127.0.0.1 --port 3306 file1.csv file2.csv

Connection defaults to env vars: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
"""

import argparse
import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text


COLUMN_MAP = {
    'EVENT_ID':        'id',
    'BEGIN_DATE_TIME': 'event_date',
    'STATE':           'state',
    'CZ_NAME':         'county',
    'TOR_F_SCALE':     'scale',
    'BEGIN_LOCATION':  'location',
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id           INT          NOT NULL,
    event_date   DATE         NOT NULL,
    state        VARCHAR(100) NOT NULL,
    county       VARCHAR(100) NOT NULL,
    scale        VARCHAR(3),
    location     VARCHAR(100),
    PRIMARY KEY (id),
    INDEX idx_state (state)
)
"""


def get_engine(host, port, user, password):
    uri = f'mysql+pymysql://{user}:{password}@{host}:{port}/tornado_events'
    return create_engine(uri, pool_pre_ping=True)


def parse_file(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, compression='infer', low_memory=False)

    if 'EVENT_TYPE' not in df.columns:
        print(f'  Skipping {path}: EVENT_TYPE column not found.')
        return pd.DataFrame()

    df = df[df['EVENT_TYPE'] == 'Tornado'].copy()
    if df.empty:
        print(f'  No tornado events in {path}.')
        return df

    missing = [c for c in COLUMN_MAP if c not in df.columns]
    if missing:
        print(f'  Warning: missing columns {missing} in {path} — filling with None.')

    df = df.rename(columns=COLUMN_MAP)
    df = df[list(COLUMN_MAP.values())].copy()

    df['event_date'] = pd.to_datetime(df['event_date'], format='mixed', dayfirst=False).dt.date
    df['state']  = df['state'].str.upper().str.strip()
    df['county'] = df['county'].str.title().str.strip()
    df['scale']  = df['scale'].str.strip().replace('', None)
    df['location'] = df['location'].str.strip().replace('', None)

    df = df.dropna(subset=['id', 'event_date', 'state', 'county'])
    df = df.where(pd.notna(df), other=None)
    return df


def import_file(path: str, engine) -> int:
    print(f'Processing {path}...')
    df = parse_file(path)
    if df.empty:
        return 0

    rows = df.to_dict(orient='records')
    inserted = 0

    with engine.begin() as conn:
        for row in rows:
            conn.execute(text("""
                INSERT INTO events (id, event_date, state, county, scale, location)
                VALUES (:id, :event_date, :state, :county, :scale, :location)
                ON DUPLICATE KEY UPDATE
                    event_date = VALUES(event_date),
                    state      = VALUES(state),
                    county     = VALUES(county),
                    scale      = VALUES(scale),
                    location   = VALUES(location)
            """), row)
            inserted += 1

    return inserted


def main():
    parser = argparse.ArgumentParser(description='Import NOAA tornado events into MySQL.')
    parser.add_argument('files', nargs='+', help='StormEvents CSV or CSV.GZ files')
    parser.add_argument('--host',     default=os.environ.get('DB_HOST', '127.0.0.1'))
    parser.add_argument('--port',     default=int(os.environ.get('DB_PORT', 3306)), type=int)
    parser.add_argument('--user',     default=os.environ.get('DB_USER', 'flask_user'))
    parser.add_argument('--password', default=os.environ.get('DB_PASSWORD', ''))
    args = parser.parse_args()

    engine = get_engine(args.host, args.port, args.user, args.password)

    with engine.begin() as conn:
        conn.execute(text(CREATE_TABLE_SQL))
    print('Table ready.')

    total = 0
    for path in args.files:
        count = import_file(path, engine)
        print(f'  Inserted/updated {count} records.')
        total += count

    print(f'\nDone. Total records processed: {total}')


if __name__ == '__main__':
    main()
