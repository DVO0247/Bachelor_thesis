import socket
import time
from datetime import datetime, timedelta
import sqlite3
import threading
import os
from typing import Optional
from colorama import Fore
import gc

# connection
#HOST = '192.168.137.1'
#HOST = '192.168.214.144'
HOST = '0.0.0.0'
PORT = 666

# timeouts
NAME_TIMEOUT = 3
NAME_TIMEOUT_COUNT = 3

# data
DATA_ENC = 'ascii'
DATA_FIELD_SEPARATOR = ','
DATA_END_CHAR = '|'
COMMIT_PERIOD = 1

# database
SENSOR_DB_CACHE_SIZE = 100_000 # kB
MASTER_DB_PATH = '.\\db.sqlite3' # Django DB for example
SENSOR_NODE_TABLE = 'web_device'

def get_path_from_name(name:str)->str:
    def get_device_info_from_name(name:str, fields:str) -> str:
        return f"""
            select {fields} from {SENSOR_NODE_TABLE}
            where name == '{name.strip()}'
            limit 1
        """
    db_path = ''
    try:
        django_conn = sqlite3.connect(MASTER_DB_PATH) # TODO: make this read-only open
        django_cur = django_conn.cursor()
        
        result = django_cur.execute(get_device_info_from_name(name, "path")).fetchone() # TODO: Handle sqlite3.OperationalError
        if result is not None:
            db_path = result[0] # TODO: more fields
    except Exception as error:
        print(error)
    finally:
        django_cur.close()
        django_conn.close()
        return db_path

def insert_values() -> str:
    return "insert into data values(null,?,?)"

def connect_db(db_path):
    conn = sqlite3.connect(db_path, autocommit=False, check_same_thread=False)
    cur = conn.cursor()
    #cur.execute("pragma synchronous=normal")
    cur.execute(f"PRAGMA cache_size = -{SENSOR_DB_CACHE_SIZE};")
    return conn, cur

class Connection:
    def __init__(self) -> None: 
        self.name : Optional[str] = None
        self.buffer = ''
        self.name_requested_time : Optional[float] = None
        self.name_requested_count = 0
        self.db_conn : Optional[sqlite3.Connection] = None
        self.db_cur : Optional[sqlite3.Cursor] = None
        self.start_millis : Optional[int] = None
        self.start_datetime : Optional[datetime] = None
        self.ignore = False # if error occure
        self.buffer_lock = threading.Lock()
        self.last_write = time.time()
        # TODO:Last recv a timeout

    def millis_to_timestamp(self, millis_now:int) -> str:
        if self.start_millis is None or millis_now < self.start_millis:
            self.start_datetime = datetime.now()
            self.start_millis = millis_now
        # TODO: vyřešit přetečení millis v Arduinu
        return (self.start_datetime + timedelta(milliseconds=millis_now-self.start_millis)).isoformat(' ', 'milliseconds')

    def connect_new_db(self) -> bool: #path/name/self.neco nevim
        self.close()
        path = get_path_from_name(self.name)
        if path != '':
            self.db_conn, self.db_cur = connect_db(path)
            return True
        else:
            self.ignore = True
            with self.buffer_lock:
                self.buffer = ''
            return False

    def close(self):
        if self.db_conn is not None:
            self.db_cur.close()
            self.db_conn.close()

connections_lock = threading.Lock()
connections : dict[tuple[str,int], Connection] = {}
def connection_loop():
    global connections
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(1000)
        s.bind((HOST, PORT))
        while True:
            #print([obj.name for obj in gc.get_objects() if isinstance(obj, Connection)], end='\r')
            recv, addr = s.recvfrom(4096)
            with connections_lock:
                if addr not in connections.keys():
                    connections[addr] = Connection()
                if connections[addr].ignore:
                    continue
                if connections[addr].name is None:
                    if connections[addr].name_requested_count <= NAME_TIMEOUT_COUNT:
                        if (connections[addr].name_requested_time is None
                            or time.time() - connections[addr].name_requested_time >= NAME_TIMEOUT):
                            s.sendto(b'\x00', addr)
                            connections[addr].name_requested_time = time.time()
                            connections[addr].name_requested_count += 1

                    elif time.time() - connections[addr].name_requested_time >= NAME_TIMEOUT:
                        connections[addr].ignore = True
                        with connections[addr].buffer_lock:
                            connections[addr].buffer = ''
                        print(f'{Fore.RED}NAME REQUEST TIMEOUT{Fore.WHITE}',addr, connections[addr].name)
                        continue

                with connections[addr].buffer_lock:
                    connections[addr].buffer += recv.decode(DATA_ENC)


db_loop_run = True
def db_loop():
    global connections
    last_commit_time = time.time()
    while db_loop_run:
        with connections_lock:
            temp_connections = tuple(connections.items())
        for addr, connection in temp_connections:
            '''now = time.time()
            if now - connection.last_write < 0.01:
                continue
            connection.last_write = now'''
            with connection.buffer_lock:
                temp_buffer = connection.buffer
                connection.buffer = ''
            if temp_buffer == '':
                continue
            splitted_buffer = temp_buffer.split(DATA_END_CHAR)[:-1]
            batch_data = []
            for data in splitted_buffer:
                if data == '':
                    with connection.buffer_lock:
                        raise Exception(f'{addr} Data content is empty\n{connection.buffer.split(DATA_END_CHAR)}')
                elif data[0] == '!':
                    new_name = data.split('!')[1].split(DATA_END_CHAR)[0]
                    if connection.name != new_name:
                        # check if name is already in dict
                        with connections_lock:
                            for _addr, _connection in connections.items():
                                if _connection.name == new_name:
                                    connections[_addr].close()
                                    connections.pop(_addr)
                                    print(f'{Fore.YELLOW}CLOSED{Fore.WHITE}',_addr, _connection.name)
                                    break
                        connection.name = new_name
                        if connection.connect_new_db():
                            print(f'{Fore.GREEN}OPENED{Fore.WHITE}', addr, connection.name)
                        else:
                            print(f'{Fore.RED}DB PATH NOT FOUND{Fore.WHITE}', addr, connection.name)
                        
                else:
                    try:
                        sensor_id, millis, value = data.split(DATA_FIELD_SEPARATOR)
                    except ValueError as error:
                        print(f'{addr} {error}\n{data}')
                        continue
                    try:
                        timestamp = connection.millis_to_timestamp(int(millis))
                    except ValueError as error:
                        print(f'{addr} {error}\n{data}')
                        continue
                    batch_data.append((timestamp, value))

            if len(batch_data) > 0 and connection.db_conn is not None:
                #print(len(batch_data), end="\r")
                connection.db_cur.executemany(insert_values(), batch_data)

        now = time.time()
        if now - last_commit_time >= COMMIT_PERIOD:
            last_commit_time = now
            with connections_lock:
                temp_connections = tuple(connections.items())
            for addr, connection in temp_connections:
                if connection.db_conn is not None:
                    connection.db_conn.commit()

        


if __name__ == '__main__':
    db_loop_thread = threading.Thread(target=db_loop, daemon=True)
    db_loop_thread.start()

    try:
        connection_loop()

    except KeyboardInterrupt:
        print("Ending...")

    finally:
        db_loop_run = False
        while db_loop_thread.is_alive():
            pass
        with connections_lock:
            for _addr, connection in tuple(connections.items()):
                if connection.db_conn is not None:
                    connection.db_conn.commit()
                    connection.db_cur.execute('pragma optimise')
                    #connection.db_cur.execute('pragma vacuum')
                    connection.db_conn.commit()
                    connection.db_cur.close()
                    connection.db_conn.close()
                connections.pop(_addr)
                print(f'{Fore.YELLOW}CLOSED{Fore.WHITE}',_addr, connection.name)
