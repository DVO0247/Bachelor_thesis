CREATE_DATA_TABLE = """
    create table if not exists data(
        id INTEGER PRIMARY KEY,
        ts INTEGER,
        value REAL
    )
"""

CREATE_TIMESTAMP_INDEX = "CREATE INDEX 'idx_ts' ON data (ts DESC)"
