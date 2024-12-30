import socket
import time
from colorama import Fore, Back
import sqlite3
import threading
from pathlib import Path
from typing import TypeAlias
import os

import sensor_node_protocol as snp
import control_center_queries as ccq

IP = '0.0.0.0'
PORT = 666
INFO_REQUEST_TIMEOUT = 1
INFO_MAX_REQUESTS = 3

MEASUREMENT_DB_CACHE_SIZE = 100_000 # kB

Addr: TypeAlias = tuple[str, int] # (ip, port)

class FreqCounter:
    def __init__(self, measure_period) -> None:
        self.measure_period = measure_period
        self.count = -1
        self.count_lock = threading.Lock()
        self.last = -1
        self._running = False
        self.log_loop_thread = threading.Thread(target=self.log_loop)

    def start(self):
        self.count = 0
        self._running = True
        self.log_loop_thread.start()

    def stop(self):
        self._running = False

    def log_loop(self):
        while self._running:
            time.sleep(self.measure_period)
            with self.count_lock:
                freq = self.count/self.measure_period
                self.count = 0
            print('freq:', freq)

    def __add__(self, count:int):
        with self.count_lock:
            self.count += count
        return self

class MeasurementDB:
    def __init__(self, path:Path) -> None:
        self.path = path
        self.conn:sqlite3.Connection
        self.cur:sqlite3.Cursor
        self._connect_db()

    def __del__(self):
        self._close_db()

    def write_to_db(self, unix_samples:tuple[tuple[int,float], ...]):
        self.cur.executemany("insert into data values(null,?,?)",unix_samples)

    def commit(self):
        self.conn.commit()

    def _connect_db(self):        
        '''
        #cur.execute("pragma synchronous=normal")
        _conn.execute(f"PRAGMA journal_mode = WAL")
        sql = """
            create table if not exists data(
                id INTEGER PRIMARY KEY,
                time INTEGER,
                value REAL
        ) 
        """
        _cur.execute(sql)
        _conn.commit()
        _conn.close()
        '''

        self.conn = sqlite3.connect(self.path.resolve(), autocommit=False, check_same_thread=False)
        self.cur = self.conn.cursor()
        self.cur.execute(f"PRAGMA cache_size = -{MEASUREMENT_DB_CACHE_SIZE};")
        self.conn.commit()

    def _close_db(self):
        self.conn.commit()
        self.conn.close()


class Sensor:
    def __init__(self) -> None:
        self.samples_buffer:list[snp.Sample] = []
        self.buffer_lock = threading.Lock()
        self.measurement_dbs:list[MeasurementDB] = []
        self.sample_period_ms:int|None = None
        self.samples_per_packet:int|None = None
        
    def add_to_buffer(self, samples:tuple[snp.Sample, ...]):
        with self.buffer_lock:
            self.samples_buffer.extend(samples)

    def update_measurements(self, sensor_node_id:int, sensor_id:int):
        new_paths = ccq.get_paths_for_sensor(sensor_node_id, sensor_id)

        # remove old paths
        for db in self.measurement_dbs:
            if db.path not in new_paths:
                self.measurement_dbs.remove(db)

        # add new paths
        current_paths = tuple(db.path for db in self.measurement_dbs)
        for path in new_paths:
            if path not in current_paths:
                self.measurement_dbs.append(MeasurementDB(path))
            
    def write_to_db(self, sensor_node_id:int, sensor_id:int, unix_time_at_zero:int):
        self.update_measurements(sensor_node_id, sensor_id)
        with self.buffer_lock:
            if self.samples_buffer:
                unix_samples = tuple((sample.timestamp+unix_time_at_zero, sample.value) for sample in self.samples_buffer)
                self.samples_buffer.clear()
            else:
                return
            for db in self.measurement_dbs:
                db.write_to_db(unix_samples)
        

class SensorNode:
    def __init__(self) -> None:
        self.name:str|None = None
        self.id:int|None = None
        self.sensor_count:int|None = None
        self.sensors:tuple[Sensor,...]|None = None
        self.unix_time_at_zero:int|None = None 
        self.info_requested_time:float|None = None
        self.initialized:bool = False
        
        self.buffer_lock = threading.Lock()
        #self.last_write = time.time()

    def begin(self, info:snp.ClientMessage.Info) -> bool:
        self.name = info.name
        self.sensor_count = info.sensor_count
        self.sensors = tuple(Sensor() for _ in range(self.sensor_count))
        self.unix_time_at_zero = info.unix_time_at_zero
        self.id = ccq.get_sensor_node_id_or_create(self.name, self.sensor_count)
        if self.id is not None:
            self.update_init_state()
            return True
        else:
            return False

    def add_to_buffer(self, sensor_samples:snp.ClientMessage.SensorSamples):
        self.sensors[sensor_samples.sensor_id].add_to_buffer(sensor_samples.samples) # type: ignore

    def update_init_state(self) -> None:
        self.initialized = ccq.get_init_state(self.id) # type: ignore

    def commit_all(self) -> None:
        for sensor in self.sensors: # type: ignore
            for db in sensor.measurement_dbs:
                db.commit()


class Server:
    def __init__(self, ip:str=IP, port:int=PORT) -> None:
        self.ip = ip
        self.port = port
        self.sensor_nodes:dict[Addr, SensorNode] = dict()
        self.sensor_nodes_lock = threading.Lock()
        self.set_param_requests:set[tuple[Addr,int]] = set() # (addr, sensor index)
        self.set_param_requests_lock = threading.Lock()
        self.waiting_for_ack:set[tuple[Addr,int]] = set() # (addr, sensor index)
        self.freq_counter = FreqCounter(5)
        self._running = False
        
        
    def connection_loop(self, use_freq_counter = False):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(1000)
            s.bind((self.ip, self.port))
            print(f'Server running on {self.ip}:{self.port}')
            if use_freq_counter:
                self.freq_counter.start()
            while self._running:
                recv, addr = s.recvfrom(4096)
                sensor_node = self.sensor_nodes.get(addr)
                if not sensor_node:
                    with self.sensor_nodes_lock:
                        sensor_node = SensorNode()
                        self.sensor_nodes[addr] = sensor_node
                    print('New connection from ', addr)
                #print(recv)
                message = snp.ClientMessage.from_bytes(recv)
                #print("Message:",message)

                if isinstance(message, snp.ClientMessage.Info):
                    sensor_node.begin(message)
                    print(f'{addr} -> {sensor_node.name} {sensor_node.sensor_count}')
                    print()

                elif not sensor_node.name:
                    if not sensor_node.info_requested_time or time.time() - sensor_node.info_requested_time >= INFO_REQUEST_TIMEOUT:
                        print(f'Request info to: {addr}')
                        s.sendto(snp.ServerMessage.RequestInfo._bytes, addr)
                        sensor_node.info_requested_time = time.time()
                
                elif isinstance(message, snp.ClientMessage.ACK):
                    self.waiting_for_ack.remove((addr, message.sensor_id))

                elif isinstance(message, snp.ClientMessage.SensorSamples) and sensor_node.initialized:
                    #print(tuple(sample.timestamp_to_iso(sensor_node.unix_time_at_zero) for sample in message.samples))
                    if (addr, message.sensor_id) not in self.waiting_for_ack:
                        if use_freq_counter:
                            self.freq_counter+=len(message.samples)
                        sensor_node.add_to_buffer(message)
                    else:
                        print('Rejected, waiting for ACK')

                with self.set_param_requests_lock:
                    _set_param_requests = frozenset(self.set_param_requests)
                for request in _set_param_requests:
                    addr, sensor_i = request
                    with self.sensor_nodes_lock:
                        sensor_node = self.sensor_nodes[addr]
                    sample_period_ms = sensor_node.sensors[sensor_i].sample_period_ms # type: ignore
                    samples_per_packet = sensor_node.sensors[sensor_i].samples_per_packet # type: ignore
                    
                    s.sendto(snp.ServerMessage.SetSensorParameters(sensor_i, sample_period_ms, samples_per_packet).to_bytes(), addr) # type: ignore
                    print(f'Request set parameters for sensor {sensor_i} ({sample_period_ms}, {samples_per_packet}) to: {addr}')
                    self.waiting_for_ack.add(request)
                    with self.set_param_requests_lock:
                        self.set_param_requests.remove(request)

    def db_operations_loop(self):
        COMMIT_PERIOD = 1
        CHECK_PARAMS_AND_INIT_PERIOD = 2
        last_commits = last_inits_and_params = time.time()
        while self._running:
            with self.sensor_nodes_lock:
                _sensor_nodes = tuple(self.sensor_nodes.values())
            if time.time() - last_inits_and_params >= CHECK_PARAMS_AND_INIT_PERIOD:
                self.check_inits(_sensor_nodes)
                self.check_params()
                last_inits_and_params = time.time()
                
            initialized_sensor_nodes = tuple(sensor_node for sensor_node in _sensor_nodes if sensor_node.initialized)
            
            self.write_to_dbs(initialized_sensor_nodes)
            
            if time.time() - last_commits >= COMMIT_PERIOD:
                self.do_db_commits(initialized_sensor_nodes)
                self.last_commits = time.time()

            time.sleep(0.001)

    def start(self, use_freq_counter=False):
        self._running = True
        threading.Thread(target=self.db_operations_loop, name='db_operations_loop').start()
        self.connection_loop(use_freq_counter)

    def stop(self):
        self._running = False
        self.freq_counter.stop()

    def check_inits(self, _sensor_nodes:tuple[SensorNode,...]):
        for sensor_node in _sensor_nodes:
            sensor_node.update_init_state()
            if sensor_node.initialized is None:
                with self.sensor_nodes_lock:
                    for addr, dict_sensor_node in self.sensor_nodes.items():
                        if dict_sensor_node == sensor_node:
                            self.sensor_nodes.pop(addr)
                            print(f'{addr} {sensor_node.name} removed')
                            break

    def write_to_dbs(self, _sensor_nodes:tuple[SensorNode,...]):
        for sensor_node in _sensor_nodes:
            try:
                for i in range(len(sensor_node.sensors)): # type: ignore
                    sensor_node.sensors[i].write_to_db(sensor_node.id, i, sensor_node.unix_time_at_zero) # type: ignore
            except Exception as e:
                with self.sensor_nodes_lock:
                    for addr, dict_sensor_node in self.sensor_nodes.items():
                        if dict_sensor_node == sensor_node:
                            self.sensor_nodes.pop(addr)
                            print(f'{addr} {sensor_node.name} removed')
                            break
                print(e)


    def do_db_commits(self, _sensor_nodes:tuple[SensorNode,...]):
        for sensor_node in _sensor_nodes:
            sensor_node.commit_all()

    def check_params(self):
        with self.sensor_nodes_lock:
            _sensor_nodes:dict[Addr, SensorNode] = dict(self.sensor_nodes)
        for addr, sensor_node in _sensor_nodes.items():
            if not (sensor_node.initialized and sensor_node.id):
                continue
            new_params = ccq.get_params_for_sensors(sensor_node.id)
            if sensor_node.sensors and new_params and len(sensor_node.sensors) == len(new_params):
                for i in range(len(sensor_node.sensors)):
                    if sensor_node.sensors[i].sample_period_ms != new_params[i][0] or sensor_node.sensors[i].samples_per_packet != new_params[i][1]:
                        with self.set_param_requests_lock:
                            sensor_node.sensors[i].sample_period_ms = new_params[i][0]
                            sensor_node.sensors[i].samples_per_packet = new_params[i][1]
                            self.set_param_requests.add((addr,i))
            else:
                raise Exception(f'In db for {sensor_node.id}, data: {sensor_node.sensors}, {new_params}')
                

if __name__ == '__main__':
    server = Server()
    try:
        server.start(use_freq_counter=True)
    except KeyboardInterrupt:
        print(f'Exiting...')
        server.stop()
        
