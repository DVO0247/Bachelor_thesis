import struct
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

ENC = 'ascii'
MAX_SAMPLES_PER_PACKET = 121

class MessageTypeByte:
    class Server:
        REQUEST_INFO = 0x00
        SET_SENSOR_PARAMETERS = 0x01
    class Client:
        KEEP_ALIVE = 0x00
        INFO = 0x01
        SENSOR_SAMPLES = 0x02
        ACK = 0x03

@dataclass
class Sample:
    timestamp:int
    value:float
    SIZE:ClassVar = 12

    @classmethod
    def from_bytes(cls, sample_bytes:bytes):
        timestamp:int = int.from_bytes(sample_bytes[:4], byteorder='little')
        value:float = struct.unpack('<d', sample_bytes[4:12])[0]
        return cls(timestamp, value)

    def timestamp_to_iso(self, unix_time_at_zero:int):
        return datetime.fromtimestamp((self.timestamp + unix_time_at_zero)/1000).isoformat(' ', 'milliseconds')
    
    def sample_to_unix_tuple(self, unix_time_at_zero:int) -> tuple[int,float]:
        return self.timestamp+unix_time_at_zero, self.value

class ServerMessage:
    @dataclass
    class Base(ABC):
        MESSAGE_TYPE_BYTE:ClassVar[int]

        @abstractmethod
        def to_bytes(self) -> bytes:
            pass

    @dataclass
    class RequestInfo(Base):
        MESSAGE_TYPE_BYTE = MessageTypeByte.Server.REQUEST_INFO
        _bytes:ClassVar = MESSAGE_TYPE_BYTE.to_bytes(1, byteorder='little')

        def to_bytes(self) -> bytes:
            return self._bytes

    @dataclass
    class SetSensorParameters(Base):
        sensor_id:int
        sample_period_ms:int
        samples_per_packet:int

        MESSAGE_TYPE_BYTE = MessageTypeByte.Server.SET_SENSOR_PARAMETERS
        
        def to_bytes(self) -> bytes:
            if self.samples_per_packet > MAX_SAMPLES_PER_PACKET:
                raise Exception(F'Max samples per packet is {MAX_SAMPLES_PER_PACKET}')
            else:
                return self.MESSAGE_TYPE_BYTE.to_bytes(1, byteorder='little') + self.sensor_id.to_bytes(1, byteorder='little') + self.sample_period_ms.to_bytes(4, byteorder='little') + self.samples_per_packet.to_bytes(1, byteorder='little')


class ClientMessage:
    @dataclass
    class Base(ABC):
        MESSAGE_TYPE_BYTE:ClassVar[int]

        @classmethod
        @abstractmethod
        def from_bytes(cls, _bytes:bytes)->"ClientMessage.Base":
            pass
        

    @dataclass
    class KeepAlive(Base):
        MESSAGE_TYPE_BYTE = MessageTypeByte.Client.KEEP_ALIVE

        @classmethod
        def from_bytes(cls, _bytes: bytes|None = None):
            return cls()


    @dataclass   
    class Info(Base):
        name:str
        sensor_count:int
        unix_time_at_zero:int

        MESSAGE_TYPE_BYTE = MessageTypeByte.Client.INFO

        @classmethod
        def from_bytes(cls, _bytes:bytes):
            i = 1
            name_length = _bytes[i]
            i += 1
            name = _bytes[i:i+name_length].decode(ENC)
            i += name_length
            sensor_count = _bytes[i]
            i+=1
            unix_time_at_zero = int.from_bytes(_bytes[i:i+8], byteorder='little')
            return cls(name, sensor_count, unix_time_at_zero)


    @dataclass
    class SensorSamples(Base):
        sensor_id:int
        samples:list[Sample]

        MESSAGE_TYPE_BYTE = MessageTypeByte.Client.SENSOR_SAMPLES

        @classmethod
        def from_bytes(cls, _bytes:bytes):
            i = 1
            sensor_id:int = _bytes[i]
            i += 1
            sample_count:int = _bytes[i]
            i += 1
            if len(_bytes) < i + sample_count*Sample.SIZE:
                raise Exception('SensorSample message is not complete')
            samples:list[Sample] = [Sample.from_bytes(_bytes[j:j+Sample.SIZE]) for j in range(i, i+sample_count*Sample.SIZE, Sample.SIZE)]
            return cls(sensor_id, samples)


    @dataclass
    class ACK(Base):
        sensor_id:int
        
        @classmethod
        def from_bytes(cls, _bytes: bytes):
            return cls(_bytes[1])
        

    @classmethod
    def from_bytes(cls, _bytes:bytes) -> Base|None:
        for subcls in cls.Base.__subclasses__():
            if subcls.MESSAGE_TYPE_BYTE == _bytes[0]:
                return subcls.from_bytes(_bytes)
        return None
