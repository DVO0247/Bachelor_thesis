import socket
from datetime import datetime, timedelta
import time
from typing import Optional
from colorama import Fore, Back
import sqlite3
import threading
from pathlib import Path

import sensor_node_protocol as snp
import control_center_queries as cc

HOST = '0.0.0.0'
PORT = 666
STRING_ENC = 'ascii'
INFO_REQUEST_TIMEOUT = 1
INFO_MAX_REQUESTS = 3

SENSOR_NODE_DB_CACHE_SIZE = 100_000 # kB
#MASTER_DB_PATH = r'./db.sqlite3' # Django DB for example

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

class MeasurementDB:
    def __init__(self, db_path:Path|str) -> None:
        self.path = db_path
        self.conn : Optional[sqlite3.Connection] = None
        self.cur : Optional[sqlite3.Cursor] = None
        self.connect_db()

    def connect_db(self) -> bool: #path/name/self.neco nevim
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
        ...

class Sensor:
    def __init__(self) -> None:
        self.samples_buffer:list[snp.Sample] = []
        self.measurement_dbs:list[MeasurementDB] = []
        
    def add_to_buffer(self, samples:tuple[snp.Sample, ...]):
        for sample in samples:
            pass

    def write_to_dbs(self, sensor_node_name:str, sensor_id:int):
        new_paths = cc.get_paths_for_sensor(sensor_node_name, sensor_id)
        for db in self.measurement_dbs[:]:
            if db.path not in new_paths:
                db.close()
                self.measurement_dbs.remove(db)

        paths = tuple(db.path for db in self.measurement_dbs)
        for new_path in new_paths:
            if new_path not in paths:
                self.measurement_dbs.append(MeasurementDB(new_path))

        ... # TODO:writes


class SensorNodeClient(Client):
    def __init__(self) -> None:
        self.name:Optional[str] = None
        self.sensor_count:Optional[int] = None
        self.sensors:Optional[tuple[Sensor,...]] = None
        self.info_requested_time:Optional[float] = None
        
        
        self.buffer_lock = threading.Lock()
        self.last_write = time.time()

    def start(self, info:snp.Info):
        self.name = info.name
        self.sensor_count = info.sensor_count
        self.sensors = tuple(Sensor() for _ in range(self.sensor_count))

    def millis_to_timestamp(self, millis_now:int) -> str:
        if self.start_millis is None or millis_now < self.start_millis:
            self.start_datetime = datetime.now()
            self.start_millis = millis_now
        # TODO: vyřešit přetečení millis v Arduinu
        return (self.start_datetime + timedelta(milliseconds=millis_now-self.start_millis)).isoformat(' ', 'milliseconds')
        
    def close(self):
        if self.db_conn is not None:
            self.db_cur.close()
            self.db_conn.close()


    def add_to_buffer(self, data:snp.Data):
        self.sensors[data.sensor_id].add_to_buffer(data.samples) # type: ignore

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
            
            message: snp.Data|snp.Info|snp.ACK = snp.get_message_from_bytes(recv)

            if isinstance(message, snp.Info):
                client.sensor_count = message.sensor_count
                client.name = message.name         

                print(f'{addr} -> {client.name} {client.sensor_count}')
                print()

            elif not client.name:
                if not client.info_requested_time or time.time() - client.info_requested_time >= INFO_REQUEST_TIMEOUT:
                    print('request')
                    s.sendto(snp.INFO_REQUEST_MESSAGE, addr)
                    client.info_requested_time = time.time()
            
            elif isinstance(message,snp.Data):
                client.add_to_buffer(message)

if __name__ == '__main__':  
    connection_loop()
                
           
