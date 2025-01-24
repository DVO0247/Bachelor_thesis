import socket
import time
import threading
from typing import TypeAlias, Iterable
from colorama import Fore, Back

import tcp_sensor_node_protocol as snp
import fbguard_protocol as fbg
import control_center_queries as ccq
from api_clients import influxdb

HOST = '0.0.0.0'
PORT = 666

RECV_SIZE = 4096
# MAX_INFO_FRAGMENTATION = 5
SENSOR_PARAMS_UPDATE_PERIOD = 1

Addr: TypeAlias = tuple[str, int]  # (ip, port)


class FreqCounter:
    def __init__(self, measure_period) -> None:
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


class Client:
    def __init__(self, server: 'Server', c: socket.socket, addr: Addr) -> None:
        self.server = server
        self.c = c
        self.addr = addr


class SensorNode(Client):
    ADDITIONAL_TIMEOUT = 5

    def __init__(self, server: 'Server', c: socket.socket, addr: Addr, snp_info: snp.Info) -> None:
        super().__init__(server, c, addr)
        self.name = snp_info.name
        self.sensor_count = snp_info.sensor_count
        self.unix_time_at_zero = snp_info.unix_time_at_zero
        self.run = True
        self.id: int
        self.sensor_params_list: list[ccq.NamedSensorParams]
        self.expected_sizes: tuple[int, ...]
        thread = threading.Thread(target=self.serve, name=self.name)
        thread.start()

    def serve(self):
        try:
            with self.c:
                id = ccq.get_sensor_node_id_or_create(
                    self.name, self.sensor_count)
                if id:
                    self.id = id
                    del id
                else:
                    return
                while not (sensor_params_list := ccq.get_params_for_sensors(self.id)):
                    time.sleep(SENSOR_PARAMS_UPDATE_PERIOD)
                self.sensor_params_list = sensor_params_list
                del sensor_params_list

                self.c.settimeout(
                    max(
                        (param.sample_period_ms/1000)*param.samples_per_packet +
                        self.ADDITIONAL_TIMEOUT for param in self.sensor_params_list
                    )
                )
                self.expected_sizes = tuple(
                    snp.SensorSamples.get_expected_size(param.samples_per_packet)
                    for param in self.sensor_params_list
                )

                self.c.send(snp.SetSensorParams(
                    self.sensor_params_list).to_bytes())

                recv_buffer = bytes()
                last_sensor_params_update = time.time()
                while self.run:
                    recv_buffer += self.c.recv(RECV_SIZE)
                    sensor_samples_list, recv_buffer = snp.SensorSamples.list_from_bytes_with_remainder( recv_buffer, self.expected_sizes)
                    # print(sensor_samples_list)
                    for project_name, measurement_id in ccq.get_running_projects(self.id).items():
                        points = [
                            influxdb.create_point(
                                measurement_id,
                                self.name,
                                self.sensor_params_list[sensor_samples.sensor_id].name,
                                sample.timestamp_to_unix(
                                    self.unix_time_at_zero),
                                sample.value,
                                write_precision='ms'
                            )
                            for sensor_samples in sensor_samples_list
                            for sample in sensor_samples.samples
                        ]
                        influxdb.write(project_name, points)

                    # checks if params updated
                    if time.time() - last_sensor_params_update >= SENSOR_PARAMS_UPDATE_PERIOD:
                        if ccq.get_params_for_sensors(self.id) != self.sensor_params_list:
                            self.stop()
                        else:
                            last_sensor_params_update = time.time()

        finally:
            self.run = False
            self.server.remove_client(self)
            print(f'{self.addr} - {self.name} disconnected')

    def stop(self):
        self.run = False


class Server:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._clients: list['Client'] = []
        self._clients_lock = threading.Lock()

    def add_client(self, client: Client):
        with self._clients_lock:
            self._clients.append(client)

    def remove_client(self, client: Client):
        with self._clients_lock:
            self._clients.remove(client)

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.settimeout(60*5)
            s.listen(5)
            print(f"Server is listening on {HOST}:{PORT}")

            while True:
                try:
                    c, addr = s.accept()
                    print(f'{addr} connected', end=' ')
                    recv_buffer = bytes()
                    recv_buffer += c.recv(RECV_SIZE)
                except socket.timeout:
                    continue
                if recv_buffer:
                    if recv_buffer[0] == snp.STX:
                        message, recv_buffer = snp.Info.from_bytes_with_remainder(
                            recv_buffer)
                        if message:
                            print(f'as {message.name}')
                            self.add_client(SensorNode(self, c, addr, message))
                    elif recv_buffer[:3] == fbg.Header.EXPECTED_SYNC:
                        message = fbg.Message.from_bytes(recv_buffer)
                        raise NotImplementedError
                    else:
                        print(f'unknown packet:\n{recv_buffer}')
                        c.close()


if __name__ == '__main__':
    Server(HOST, PORT).run()
