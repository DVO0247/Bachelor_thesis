create_data_table = """
    create table data(
        id INTEGER primary key,
        timestamp TEXT default (datetime('now','localtime')),
        value INTEGER
    )
"""
