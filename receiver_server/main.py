import socket
import time
import threading
from typing import TypeAlias
from colorama import Fore, Back
from abc import ABC, abstractmethod
from enum import StrEnum

import tcp_sensor_node_protocol as snp
import fbguard_protocol as fbg
import control_center_queries as ccq
from api_clients import influxdb

HOST = '0.0.0.0'
PORT = 666

RECV_SIZE = 4096
SENSOR_PARAMS_UPDATE_PERIOD = 1
MAX_FIRST_MESSAGE_FRAGMENTATION = 1024
UINT32_MAX = 0xFFFFFFFF

Addr: TypeAlias = tuple[str, int]  # (ip, port)

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
            print('freq:', self.count/self.measure_period)
            with self.count_lock:
                self.count = 0

    def __add__(self, count: int):
        with self.count_lock:
            self.count += count
        return self
freq = FreqCounter(5)
freq.start()

# Abstract class
class Client(ABC):
    TYPE: ccq.SensorNodeTypes      

    def __init__(self, server: 'Server', c: socket.socket, addr: Addr, initial_recv_buffer:bytes) -> None:
        self.id: int
        self.name: str
        self.server = server
        self.c = c
        self.addr = addr
        self._run = True
        print(f'({addr[0]}:{addr[1]}) identified as {self.name}')
        self.serve(initial_recv_buffer)
        #self.server.stop_client_if_exists(self.name, self) TODO: try this

    @abstractmethod
    def serve(self, recv_buffer:bytes):
        pass

    def stop(self):
        self._run = False

    def _remove_client(self):
        self.server.remove_client(self)
        print(f'{self} - disconnected')

    def __str__(self) -> str:
        return f'({self.__class__.__name__}, {self.name}, {self.addr[0]}:{self.addr[1]})'


class ESP32(Client):
    TYPE = ccq.SensorNodeTypes.ESP32
    ADDITIONAL_TIMEOUT = 5

    def __init__(self, server: 'Server', c: socket.socket, addr: Addr, snp_info: snp.Info, recv_buffer:bytes) -> None:
        self.name = snp_info.name
        self.sensor_count = snp_info.sensor_count
        self.unix_time_offset = snp_info.unix_time_offset
        super().__init__(server, c, addr, bytes())

    def serve(self, recv_buffer:bytes):
        try:
            ready_to_time_overflow = False
            time_overflow_offset = 0
            with self.c:
                self.id = ccq.get_sensor_node_id_or_create(self.name, self.TYPE, self.sensor_count)
                
                sensor_params_list: list[ccq.NamedSensorParams]
                while not (sensor_params_list := ccq.get_params_for_sensors(self.id)):
                    time.sleep(SENSOR_PARAMS_UPDATE_PERIOD)

                self.c.settimeout(
                    max(
                        (param.sample_period_ms/1000)*param.samples_per_message +
                        self.ADDITIONAL_TIMEOUT for param in sensor_params_list
                    )
                )
                # Gets expected size for all sensor sample messages
                expected_sizes: tuple[int, ...] = tuple(
                    snp.SensorSamples.get_expected_size(param.samples_per_message)
                    for param in sensor_params_list
                )

                # Sends params for sensors
                self.c.send(snp.SetSensorParams(
                    sensor_params_list).to_bytes())

                print(f'{self} - receiving samples')
                last_sensor_params_update = time.time()
                while self._run:
                    try:
                        recv_buffer += self.c.recv(RECV_SIZE)
                    except socket.timeout:
                        print(f'{self} - timed out')
                        self.stop()
                        return
                    
                    sensor_samples_list, recv_buffer = snp.SensorSamples.list_from_bytes_with_remainder(recv_buffer, expected_sizes)
                    # print(sensor_samples_list)

                    if sensor_samples_list:
                        # Checks if ESP32 time overflowed
                        current_timestamp = sensor_samples_list[0].samples[0].timestamp
                        if not ready_to_time_overflow and current_timestamp >= UINT32_MAX//2:
                            ready_to_time_overflow = True
                        elif ready_to_time_overflow and current_timestamp < (UINT32_MAX//2)-1000: # 1000 -> safety offset 
                            ready_to_time_overflow = False
                            time_overflow_offset += UINT32_MAX
                            print(f'{self} - time overflow')
                        
                        # Creates sample points for every running project
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

                    # Checks if params updated
                    if time.time() - last_sensor_params_update >= SENSOR_PARAMS_UPDATE_PERIOD:
                        if ccq.get_params_for_sensors(self.id) != sensor_params_list:
                            print(f'{self} - params changed - restarting {self.__class__.__name__}')
                            self.stop()
                        else:
                            last_sensor_params_update = time.time()
        finally:
            self._remove_client()


class FBGuard(Client):
    TYPE = ccq.SensorNodeTypes.FBGUARD
    TIMEOUT = 60*10
    def __init__(self, server: 'Server', c: socket.socket, addr: tuple[str, int], fbguard_message:fbg.Message, recv_buffer:bytes) -> None:
        self.name = fbguard_message.header.device_id
        self.id = ccq.get_sensor_node_id_or_create(self.name, self.TYPE)
        self.sensor_names: set[str] = set(ccq.get_sensor_names(self.id))
        recv_buffer = fbguard_message.to_bytes() + recv_buffer
        super().__init__(server, c, addr, recv_buffer)

    def serve(self, recv_buffer:bytes=bytes()):
        try:
            while not ccq.is_initialized(self.id): # Probably useless
                time.sleep(SENSOR_PARAMS_UPDATE_PERIOD)

            self.c.settimeout(self.TIMEOUT)
            while self._run:
                try:
                    recv_buffer += self.c.recv(RECV_SIZE)
                except socket.timeout:
                    print(f'{self} - timed out')
                    self.stop()
                    return
                messages, recv_buffer = fbg.Message.list_from_bytes_with_remainder(recv_buffer)

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
        with self._clients_lock:
            for client in self._clients:
                if client_name == client.name and client != ignore:
                    print(f'{client} - client with this name is already connected')
                    client.stop()

    def add_client(self, client: Client):
        with self._clients_lock:
            self._clients.append(client)

    def remove_client(self, client: Client):
        with self._clients_lock:
            self._clients.remove(client)

    def handle_new_connection(self, c:socket.socket, addr:Addr):
        with c:
            print(f'New connection from ({addr[0]}:{addr[1]})')
            recv_buffer = bytes()
            for _ in range(MAX_FIRST_MESSAGE_FRAGMENTATION):
                recv_buffer += c.recv(RECV_SIZE)

                if recv_buffer[0] == snp.STX:
                    message, recv_buffer = snp.Info.from_bytes_with_remainder(
                        recv_buffer)
                    if message:
                        self.add_client(ESP32(self, c, addr, message, recv_buffer))
                        return

                elif recv_buffer[:3] == fbg.Header.EXPECTED_SYNC:
                    message, recv_buffer = fbg.Message.from_bytes_with_remainder(recv_buffer)
                    if message:
                        self.add_client(FBGuard(self, c, addr, message, recv_buffer))
                        return

                else:
                    print(f'Unknown\nReceived data:\n{recv_buffer}')
                    c.close()
                    print(f'({addr[0]}:{addr[1]}) - disconnected')
                    return

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.settimeout(60*5)
            s.listen(5)
            print(f"Server is listening on {self.host}:{self.port}")

            while True:
                try:
                    c, addr = s.accept()
                    threading.Thread(target=self.handle_new_connection, args=(c, addr)).start()
                except socket.timeout:
                    continue


if __name__ == '__main__':
    Server(HOST, PORT).run()
