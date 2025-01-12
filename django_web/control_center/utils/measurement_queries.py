import sqlite3
import os
from pathlib import Path
from datetime import datetime

class SQL:
    class Create:
        DATA_TABLE = """
            create table if not exists data(
                id INTEGER PRIMARY KEY,
                ts INTEGER,
                value REAL
            )
        """
        TIMESTAMP_INDEX = "CREATE INDEX 'idx_ts' ON data (ts DESC)"

    class Select:
        COUNT = "select count() from data"
        WITH_LIMIT = """
            select *
            from data
            limit ? offset ?
        """
        WITH_LIMIT_DESC = """
            select *
            from data
            order by id desc
            limit ? offset ?
        """

def new_measurement_db(path:Path|str):
    if os.path.exists(path):
        return

    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.execute('pragma journal_mode = WAL')
    conn.commit()

    cur.execute(SQL.Create.DATA_TABLE)
    cur.execute(SQL.Create.TIMESTAMP_INDEX)

    conn.commit()
    cur.close()
    conn.close()

def count(path:Path|str):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(SQL.Select.COUNT)
    return cur.fetchone()[0]

def select_desc(path:Path|str, count:int, page:int):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(SQL.Select.WITH_LIMIT_DESC, (count, page*count))
    return cur.fetchall()

def sequential_select(cur:sqlite3.Cursor, size:int):
    i = 0
    while samples := cur.execute(SQL.Select.WITH_LIMIT, (size, i*size)).fetchall():
        yield samples
        i += 1

def export_to_csv(db_path:Path|str, out_path:Path|str, header:bool=False, value_name:str|None = None, humam_time=False, separator=','):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    #cur.execute(f"PRAGMA cache_size = -{50_000};")
    open(out_path, 'w').close()
    with open(out_path, 'a') as file:
        if header:
            if not value_name:
                file.write(f'ID,Timestamp,{value_name if value_name else 'Value'}\n')

        for samples in sequential_select(cur, 500_000):
            for sample in samples:
                file.write(f'{sample[0]}{separator}{sample[1]}{separator}{sample[2]}\n')

if __name__ == '__main__':
    export_to_csv(
        r"C:\VSB\Bakalářská práce\DVO0247\data\28_testnevim\44_esp1\0_pi\2_2025-01-11T16-52-57.db",
        r'C:\VSB\Bakalářská práce\DVO0247\django_web\control_center\temp\export.csv',
        )