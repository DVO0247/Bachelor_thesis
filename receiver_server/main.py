"""
This module is used to handle TCP communication between the server and clients.
"""

import logging
from rich.logging import RichHandler
import os
from pathlib import Path

DEBUG = False if os.getenv('DEBUG') == 'false' else True
APP_DATA_PATH = Path(str(os.getenv('APP_DATA_PATH'))) if os.getenv('APP_DATA_PATH') else Path(__file__).parent.parent/'app_data'

if __name__ == '__main__':
    LOG_FILE_PATH = APP_DATA_PATH/'receiver_server_log.txt'

    logging.getLogger("Rx").setLevel(logging.WARNING)
    log = logging.getLogger()
    log.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    file_handler = logging.FileHandler(LOG_FILE_PATH)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    file_handler.setLevel(logging.INFO)

    stream_handler = RichHandler(rich_tracebacks=True, show_time=True)
    stream_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    log.addHandler(file_handler)
    log.addHandler(stream_handler)
else:
    log = logging.getLogger(__name__)

import socket
import time
import threading
from typing import TypeAlias
from abc import ABC, abstractmethod
import signal

import sensor_node_protocol as snp
import fbguard_protocol as fbg
import control_center_queries as ccq
from api_clients import influxdb

HOST = os.getenv('RECEIVER_HOST', '0.0.0.0')
PORT = int(os.getenv('RECEIVER_PORT', 5123))

RECV_SIZE = 4096
SENSOR_PARAMS_UPDATE_PERIOD = 1
MAX_FIRST_MESSAGE_FRAGMENTATION = 1024
CLIENT_TIMEOUT = 3
UINT32_MAX = 0xFFFFFFFF

class KeepAlive:
    INTERVAL = 15
    INTERVAL_BETWEEN_ATTEMPTS = 1
    MAX_FAILED_ATTEMPTS = 3

if DEBUG:
    from math import isnan

Addr: TypeAlias = tuple[str, int]  # (ip, port)

def thread_exception_handler(args):
    logging.error(f"Exception in thread {args.thread.name}: {args.exc_value}", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

threading.excepthook = thread_exception_handler


def handle_stop_signal(signum, frame):
    """
    This function is called when a stop signal is received (e.g., `docker stop`).
    """
    exit(0)

class FreqCounter:
    def __init__(self, measure_period:float|int) -> None:
        self.measure_period = measure_period
        self.count = -1
        self.count_lock = threading.Lock()
        self._run = False
        self.log_loop_thread = threading.Thread(target=self.log_loop)

    def start(self):
        self.count = 0
        self._run = True
        self.log_loop_thread.start()

    def stop(self):
        self._run = False

    def log_loop(self):
        while self._run:
            time.sleep(self.measure_period)
            log.debug(f'DB write freq: {self.count/self.measure_period}')
            with self.count_lock:
                self.count = 0

    def __add__(self, count: int):
        with self.count_lock:
            self.count += count
        return self
if DEBUG:
    freq = FreqCounter(5)
    freq.start()

# Abstract class
class Client(ABC):
    TYPE: ccq.SensorNodeTypes

    def __init__(self, server: 'Server', c: socket.socket, addr: Addr, initial_recv_buffer:bytes = bytes()) -> None:
        self.id: int
        self.name: str
        self.recv_buffer = initial_recv_buffer
        self.server = server
        self.c = c
        self.addr = addr
        self._run = True
        self.change_state_after_disconnect = True
        self.server.add_client(self)
        log.info(f'({addr[0]}:{addr[1]}) identified as {self.name}')
        self.server.stop_client_if_exists(self.name, self)

    @abstractmethod
    def serve(self):
        pass

    def stop(self):
        self._run = False

    def _remove_client(self):
        """Remove `Client` from `Server`"""
        self.stop()
        self.server.remove_client(self)
        if self.change_state_after_disconnect and hasattr(self, 'id'):
            ccq.set_sensor_node_conn_state(self.id, False)
        log.info(f'{self} - disconnected')

    def __str__(self) -> str:
        return f'({self.__class__.__name__}, {self.name}, {self.addr[0]}:{self.addr[1]})'


class ESP32(Client):
    TYPE = ccq.SensorNodeTypes.ESP32 # need to add to Control Center
    #ADDITIONAL_TIMEOUT = 5

    def __init__(self, server: 'Server', c: socket.socket, addr: Addr, snp_info: snp.Info) -> None:
        self.name = snp_info.name
        self.sensor_count = snp_info.sensor_count
        self.unix_time_offset = snp_info.unix_time_offset
        super().__init__(server, c, addr)

    def serve(self):
        try:
            ready_to_time_overflow = False
            time_overflow_offset = 0
            with self.c:
                self.id = ccq.get_sensor_node_id_or_create(self.name, self.TYPE, self.sensor_count)
                ccq.set_sensor_node_conn_state(self.id, True)
                
                sensor_params_list: list[ccq.NamedSensorParams]
                while not (sensor_params_list := ccq.get_params_for_sensors(self.id)):
                    time.sleep(SENSOR_PARAMS_UPDATE_PERIOD)
                '''
                self.c.settimeout(
                    max(
                        (param.sample_period_ms/1000)*param.samples_per_message +
                        self.ADDITIONAL_TIMEOUT for param in sensor_params_list
                    )
                )
                '''
                self.c.settimeout(CLIENT_TIMEOUT)
                # Gets expected size for all sensor sample messages
                expected_sizes: tuple[int, ...] = tuple(
                    snp.SensorSamples.get_expected_size(param.samples_per_message)
                    for param in sensor_params_list
                )

                # Sends params for sensors
                self.c.send(snp.SetSensorParams(
                    sensor_params_list).to_bytes())

                log.info(f'{self} - receiving samples')
                last_sensor_params_update = time.time()
                while self._run:
                    try:
                        self.recv_buffer += self.c.recv(RECV_SIZE)
                    except TimeoutError:
                        pass
                    except ConnectionResetError:
                        log.warning(f'{self} - not alive')
                        return

                    sensor_samples_list, self.recv_buffer = snp.SensorSamples.list_from_bytes_with_remainder(self.recv_buffer, expected_sizes)
                    # print(sensor_samples_list)

                    if sensor_samples_list:
                        # Checks if ESP32 time overflowed
                        current_timestamp = sensor_samples_list[0].samples[0].timestamp
                        if not ready_to_time_overflow and current_timestamp >= UINT32_MAX//2:
                            ready_to_time_overflow = True
                        elif ready_to_time_overflow and current_timestamp < (UINT32_MAX//2)-1000: # 1000 -> safety offset 
                            ready_to_time_overflow = False
                            time_overflow_offset += UINT32_MAX
                            log.info(f'{self} - time overflow')

                        if DEBUG and any(isnan(sample.value) for sensor_samples in sensor_samples_list for sample in sensor_samples.samples): # type: ignore
                            log.debug(f'{self} - NaN value detected')

                        # Creates sample points for each running project
                        for project_name, measurement_id in ccq.get_running_project_measurements(self.id):
                            points = [
                                influxdb.create_point(
                                    measurement_id,
                                    self.name,
                                    sensor_params_list[sensor_samples.sensor_id].name,
                                    sample.timestamp_to_unix(self.unix_time_offset)+time_overflow_offset,
                                    sample.value,
                                    write_precision='ms'
                                )
                                for sensor_samples in sensor_samples_list
                                for sample in sensor_samples.samples
                            ]
                            influxdb.write(project_name, points)
                            if DEBUG:
                                freq.__add__(len(points))

                    # Checks if params updated
                    if time.time() - last_sensor_params_update >= SENSOR_PARAMS_UPDATE_PERIOD:
                        if ccq.get_params_for_sensors(self.id) != sensor_params_list:
                            log.info(f'{self} - params changed - restarting {self.__class__.__name__}')
                            self.stop()
                        else:
                            last_sensor_params_update = time.time()
        finally:
            self._remove_client()


class FBGuard(Client):
    TYPE = ccq.SensorNodeTypes.FBGUARD
    TIMEOUT = 60*10 # TODO
    def __init__(self, server: 'Server', c: socket.socket, addr: tuple[str, int], fbguard_message:fbg.Message, remainder:bytes) -> None:
        self.name = fbguard_message.header.device_id
        self.id = ccq.get_sensor_node_id_or_create(self.name, self.TYPE)
        ccq.set_sensor_node_conn_state(self.id, True)
        self.sensor_names: set[str] = set(ccq.get_sensor_names(self.id))
        initial_recv_buffer = fbguard_message.to_bytes() + remainder
        super().__init__(server, c, addr, initial_recv_buffer)

    def serve(self):
        try:
            while not ccq.is_initialized(self.id): # Probably useless
                time.sleep(SENSOR_PARAMS_UPDATE_PERIOD)

            self.c.settimeout(self.TIMEOUT)
            while self._run:
                try:
                    self.recv_buffer += self.c.recv(RECV_SIZE)
                except TimeoutError:
                    pass
                except ConnectionResetError:
                    log.warning(f'{self} - not alive')
                    return
                messages, self.recv_buffer = fbg.Message.list_from_bytes_with_remainder(self.recv_buffer)
                # Checks if new names are received
                for name in (message.header.sensor_id for message in messages):
                    if name not in self.sensor_names:
                        self.sensor_names.add(name)
                        ccq.add_sensor(self.id, name)

                for project_name, measurement_id in ccq.get_running_project_measurements(self.id):
                    
                    points = [
                        influxdb.create_point(
                            measurement_id,
                            self.name,
                            message.header.sensor_id,
                            readout.timestamp_seconds*10**6 + readout.timestamp_microseconds,
                            readout.value,
                            write_precision='us'
                        )
                        for message in messages
                        for readout in message.data.readouts
                    ]

                    influxdb.write(project_name, points)
                    if DEBUG:
                        freq.__add__(len(points))
        finally:
            self._remove_client()


class Server:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._clients: list[Client] = []
        self._clients_lock = threading.Lock()

    def stop_client_if_exists(self, client_name:str, ignore:Client|None):
        """Stop client with the same name if exist"""
        with self._clients_lock:
            for client in self._clients:
                if client_name == client.name and client != ignore:
                    log.warning(f'{client} - client with this name is already connected')
                    client.change_state_after_disconnect = False
                    client.stop()

    def add_client(self, client: Client):
        with self._clients_lock:
            self._clients.append(client)

    def remove_client(self, client: Client):
        with self._clients_lock:
            self._clients.remove(client)

    def handle_new_connection(self, c:socket.socket, addr:Addr):
        with c:
            log.info(f'New connection from ({addr[0]}:{addr[1]})')
            recv_buffer = bytes()
            for _ in range(MAX_FIRST_MESSAGE_FRAGMENTATION):
                recv_buffer += c.recv(RECV_SIZE)

                if recv_buffer[0] == ESP32.TYPE.value:
                    message, recv_buffer = snp.Info.from_bytes_with_remainder(recv_buffer)
                    log.debug(message)
                    if message:
                        ESP32(self, c, addr, message).serve()
                        return

                elif recv_buffer[:3] == fbg.Header.EXPECTED_SYNC:
                    message, recv_buffer = fbg.Message.from_bytes_with_remainder(recv_buffer)
                    if message:
                        FBGuard(self, c, addr, message, recv_buffer).serve()
                        return

                else:
                    log.warning(f'Unknown\nReceived data:\n{recv_buffer}')
                    c.close()
                    log.info(f'({addr[0]}:{addr[1]}) - disconnected')
                    return

    def run(self):
        ccq.set_all_sensor_nodes_conn_state(False)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.settimeout(60*5)
            s.listen(20) # max number of pending requests
            s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1) # Enable keep-alive
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, KeepAlive.INTERVAL)   # keep-alive Interval
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, KeepAlive.INTERVAL_BETWEEN_ATTEMPTS)   # Interval between attempts
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, KeepAlive.MAX_FAILED_ATTEMPTS) # Max failed attempts
            log.info(f"Server is listening on {self.host}:{self.port}")
            while True:
                try:
                    c, addr = s.accept()
                    threading.Thread(target=self.handle_new_connection, args=(c, addr), name=str(addr)).start()
                except TimeoutError:
                    continue

        ccq.set_all_sensor_nodes_conn_state(False)

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handle_stop_signal)
    signal.signal(signal.SIGINT, handle_stop_signal)
    Server(HOST, PORT).run()
