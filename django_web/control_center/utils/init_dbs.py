import sqlite3
import os
from . import sql_queries

OVERWRITE = False

def new_measurement_db(path:str) -> bool:
    if os.path.exists(path):
        if OVERWRITE:
            os.remove(path)
        else:
            raise Exception(f'file {path} exists')

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
    return True
