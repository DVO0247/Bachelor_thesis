import socket
import tcp_sensor_node_protocol as snp
import time
from datetime import datetime
import threading
import influxdb

# Set up the server parameters
HOST = '0.0.0.0'  # Listen on all available network interfaces
PORT = 666  # Port to listen on

SAMPLES_COUNT = 89 # 119 is max
PERIOD = 1
sample_sizes = (snp.SensorSamples.get_expected_size(SAMPLES_COUNT), snp.SensorSamples.get_expected_size(1))
print(sample_sizes[0])

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

    def __add__(self, count:int):
        with self.count_lock:
            self.count+=count
        return self

# Create a new socket object
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.settimeout(60*5)
    s.listen(5)
    samples:list[snp.Sample] = []
    print(f"Server is listening on {HOST}:{PORT}")
    while True:
        c, addr = s.accept()
        print(f"Connection from {addr} has been established.")
        freq_counter = FreqCounter(5)
        freq_counter.start()
        try: 
            data = c.recv(4096)
            if not data:
                print('No SensorSamples')
                continue
            print("Received first data:")
            print(' '.join(f'{byte:02x}' for byte in data), '->', data, len(data))
            info, recv_buffer = snp.Info.from_bytes_with_remainder(data)
            print(info)
            if info:
                unix_time_at_zero = info.unix_time_at_zero
                sensor_paramss = (snp.SensorParams(PERIOD, SAMPLES_COUNT), )
                c.send(snp.SetSensorParams(sensor_paramss).to_bytes())
            else:
                continue
            last = time.perf_counter()
            while True:
                recv_buffer += c.recv(4096)
                #print("Received data:")
                data_list, recv_buffer = snp.SensorSamples.list_from_bytes_with_remainder(recv_buffer, sample_sizes)
                #print(data_list)
                if recv_buffer:
                    #print(buffer)
                    pass
                points = (
                    influxdb.create_point(0,'TestNode','pi',sample.timestamp+unix_time_at_zero,sample.value,'ms')
                    for data in data_list for sample in data.samples
                )
                influxdb.write('test',points)
                freq_counter+=SAMPLES_COUNT
                
        finally:
            c.close()

