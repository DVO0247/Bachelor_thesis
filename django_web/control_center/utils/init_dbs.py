import sqlite3
import os
from . import sql_queries

def new_measurement_db(path:str):
    if os.path.exists(path):
        return

    conn = sqlite3.connect(f'{path}')
    cur = conn.cursor()

    cur.execute('pragma journal_mode = WAL')
    conn.commit()

    cur.execute(sql_queries.CREATE_DATA_TABLE)
    cur.execute(sql_queries.CREATE_TIMESTAMP_INDEX)
    # TODO: create index
    conn.commit()
    cur.close()
    conn.close()

