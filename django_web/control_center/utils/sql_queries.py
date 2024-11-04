CREATE_DATA_TABLE = """
    create table data(
        id INTEGER primary key,
        timestamp TEXT default (datetime('now','localtime')),
        value INTEGER
    )
"""

CREATE_TIMESTAMP_INDEX = "CREATE INDEX 'idx_timestamp' ON data (timestamp DESC)"
