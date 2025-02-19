import struct
from datetime import datetime
from typing import Self, Iterable, ClassVar, Sequence
from dataclasses import dataclass

STX = 0x02  # ASCII START OF TEXT
ETX = 0x03  # ASCII END OF TEXT

ENC = 'ascii'
MAX_SAMPLES_PER_MESSAGE = 89


@dataclass
class SensorParams:
    sample_period_ms: int
    samples_per_message: int


@dataclass
class SetSensorParams:
    sensor_params_list: Iterable[SensorParams]

    def __post_init__(self):
        for params in self.sensor_params_list:
            if params.samples_per_message > MAX_SAMPLES_PER_MESSAGE:
                raise Exception(F'Max samples per message is {MAX_SAMPLES_PER_MESSAGE}')

    def to_bytes(self) -> bytes:
        return b''.join(
            struct.pack('<iB', param.sample_period_ms, param.samples_per_message)
            for param in self.sensor_params_list
        )  # little endian 4B 1B


@dataclass
class Sample:
    timestamp: int
    value: float

    SIZE: ClassVar = 12

    @classmethod
    def from_bytes(cls, sample_bytes: bytes):
        timestamp: int = int.from_bytes(sample_bytes[0:4], byteorder='little')
        value: float = struct.unpack('<d', sample_bytes[4:12])[0]
        return cls(timestamp, value)

    def timestamp_to_iso(self, unix_time_offset: int) -> str:
        return datetime.fromtimestamp((self.timestamp + unix_time_offset)/1000).isoformat(' ', 'milliseconds')

    def timestamp_to_unix(self, unix_time_offset: int) -> int:
        return unix_time_offset + self.timestamp


@dataclass
class SensorSamples:
    sensor_id: int
    samples: tuple[Sample, ...]

    @classmethod
    def from_bytes(cls, samples_bytes: bytes):
        sensor_id: int = samples_bytes[0]
        samples = tuple(Sample.from_bytes(samples_bytes[i:i+Sample.SIZE]) for i in range(1, len(samples_bytes), Sample.SIZE))
        return cls(sensor_id, samples)

    @classmethod
    def list_from_bytes_with_remainder(cls, _bytes: bytes, expected_sizes: Sequence[int]) -> tuple[list[Self], bytes]:
        cls_list: list[Self] = []
        bytes_view = memoryview(_bytes)
        # Checks if can get expected message size for sensor, then checks if bytes has at least expected size
        while len(bytes_view) > 0 and (expected_size := expected_sizes[bytes_view[0]]) <= len(bytes_view): # (bytes_view[0] -> sensor_id)
            cls_list.append(cls.from_bytes(bytes_view[:expected_size]))
            bytes_view = bytes_view[expected_size:]
        return cls_list, bytes(bytes_view)

    @staticmethod
    def get_expected_size(sample_count: int) -> int:
        return 1 + sample_count*Sample.SIZE


@dataclass
class Info:
    name: str
    sensor_count: int # 1B
    unix_time_offset: int # 8B

    UNIX_TIME_OFFSET_SIZE: ClassVar = 8
    SIZE_WITHOUT_NAME: ClassVar = 3 + UNIX_TIME_OFFSET_SIZE

    @classmethod
    def from_bytes(cls, _bytes: bytes):
        if _bytes[0] != STX:
            raise Exception('STX not found in info message')
        etx_index = _bytes.find(ETX)
        if etx_index == -1:
            raise Exception('ETX not found in info message')
        index = 1
        name = _bytes[index:etx_index].decode(ENC)
        index = etx_index + 1
        sensor_count = _bytes[index]
        index += 1
        unix_time_offset = int.from_bytes(
            _bytes[index:index+cls.UNIX_TIME_OFFSET_SIZE], byteorder='little')
        return cls(name, sensor_count, unix_time_offset)

    @classmethod
    def from_bytes_with_remainder(cls, _bytes: bytes) -> tuple[Self|None, bytes]:
        if len(_bytes) > 0 and _bytes[0] == STX:
            etx_index = _bytes.find(ETX)
            expected_size = cls.expected_size(etx_index)
            if etx_index != -1 and len(_bytes) >= (expected_size):
                return cls.from_bytes(_bytes[:expected_size]), _bytes[expected_size:]

        return None, _bytes

    @classmethod
    def expected_size(cls, etx_index):
        return etx_index - 1 + cls.SIZE_WITHOUT_NAME

