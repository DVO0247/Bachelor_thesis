import socket
from datetime import datetime, timedelta
import time
from sensor_node_protocol import *
from typing import Optional
from colorama import Fore, Back
import sqlite3
import threading
from enum import Enum

import sql_queries

HOST = '0.0.0.0'
PORT = 666
STRING_ENC = 'ascii'
INFO_REQUEST_TIMEOUT = 1
INFO_MAX_REQUESTS = 3

SENSOR_NODE_DB_CACHE_SIZE = 100_000 # kB
MASTER_DB_PATH = '.\\db.sqlite3' # Django DB for example

class SensorNodeState(Enum):
    UNKNOWN = 0
    KNOWN = 1
    INITIALIZED = 2
    
def get_state_from_name(name:str)->SensorNodeState:
    try:
        master_db_conn = sqlite3.connect(MASTER_DB_PATH) # TODO: make this read-only open
        master_db_cur = master_db_conn.cursor()
        
        sql_out = master_db_cur.execute(sql_queries.INITIALIZED_BY_SENSOR_NODE_NAME, (name,)).fetchone() # TODO: Handle sqlite3.OperationalError
        if sql_out is None:
            result = SensorNodeState.UNKNOWN
        elif sql_out[0] == 0:
            result = SensorNodeState.KNOWN
        elif sql_out[0] == 1:
            result = SensorNodeState.INITIALIZED
    except Exception as error:
        print(error)
    finally:
        master_db_cur.close()
        master_db_conn.close()
        return result

def insert_values() -> str:
    return "insert into data values(null,?,?)"

def connect_db(db_path):
    conn = sqlite3.connect(db_path, autocommit=False, check_same_thread=False)
    cur = conn.cursor()
    #cur.execute("pragma synchronous=normal")
    cur.execute(f"PRAGMA cache_size = -{SENSOR_NODE_DB_CACHE_SIZE};")
    return conn, cur

class Client:
    pass

class SensorNodeClient(Client):
    def __init__(self) -> None:
        self.name:Optional[str] = None
        self.sensor_count:Optional[int] = None
        self.info_requested_time:Optional[float] = None
        self.samples_buffer : list[Sample] = []
        self.db_conn : Optional[sqlite3.Connection] = None
        self.db_cur : Optional[sqlite3.Cursor] = None
        self.buffer_lock = threading.Lock()
        self.last_write = time.time()

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


    def add_to_buffer(self, samples:Samples):
        for sample in samples.samples:
            self.samples_buffer.append(*sample)


def connection_loop():
    clients:dict[tuple[str,int], SensorNodeClient] = dict()
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(1000)
        s.bind((HOST, PORT))
        while True:
            recv, addr = s.recvfrom(4096)
            client:Optional[SensorNodeClient] = clients.get(addr)
            if not client:
                client = clients[addr] = SensorNodeClient()
                print('New connection from ', addr)
            
            message: Samples|Info|ACK = get_message_from_bytes(recv)

            if isinstance(message, Info):
                client.sensor_count = message.sensor_count
                client.name = message.name         

                print(f'{addr} -> {client.name} {client.sensor_count}')
                print()

            elif not client.name:
                if not client.info_requested_time or time.time() - client.info_requested_time >= INFO_REQUEST_TIMEOUT:
                    print('request')
                    s.sendto(INFO_REQUEST_MESSAGE, addr)
                    client.info_requested_time = time.time()
            
            if isinstance(message,Samples):
                client.add_to_buffer(message)

if __name__ == '__main__':  
    connection_loop()
                
           
