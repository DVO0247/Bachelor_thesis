import struct
from datetime import datetime
from abc import ABC, abstractmethod

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


def auto_repr(cls):
    def __repr__(self):
        return f'{self.__class__.__name__}({self.__dict__})'
    cls.__repr__ = __repr__
    return cls



@auto_repr
class Sample:
    SIZE = 12
    def __init__(self, timestamp:int, value:float) -> None:
        self.timestamp = timestamp
        self.value = value

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
    class Base(ABC):
        MESSAGE_TYPE_BYTE:int
        @abstractmethod
        def to_bytes(self) -> bytes:
            pass


    class RequestInfo(Base):
        MESSAGE_TYPE_BYTE = MessageTypeByte.Server.REQUEST_INFO
        _bytes = MESSAGE_TYPE_BYTE.to_bytes(1, byteorder='little')
        def to_bytes(self) -> bytes:
            return self._bytes


    class SetSensorParameters(Base):
        MESSAGE_TYPE_BYTE = MessageTypeByte.Server.SET_SENSOR_PARAMETERS
        def __init__(self, sensor_id:int, sample_period_ms:int, samples_per_packet:int) -> None:
            self.sensor_id = sensor_id
            self.sample_period_ms = sample_period_ms
            self.samples_per_packet = samples_per_packet
        
        def to_bytes(self) -> bytes:
            if self.samples_per_packet > MAX_SAMPLES_PER_PACKET:
                raise Exception(F'Max samples per packet is {MAX_SAMPLES_PER_PACKET}')
            else:
                return self.MESSAGE_TYPE_BYTE.to_bytes(1, byteorder='little') + self.sensor_id.to_bytes(1, byteorder='little') + self.sample_period_ms.to_bytes(4, byteorder='little') + self.samples_per_packet.to_bytes(1, byteorder='little')



class ClientMessage:
    class Base(ABC):
        MESSAGE_TYPE_BYTE:int
        @classmethod
        @abstractmethod
        def from_bytes(cls, _bytes:bytes)->"ClientMessage.Base":
            pass
        

    class KeepAlive(Base):
        MESSAGE_TYPE_BYTE = MessageTypeByte.Client.KEEP_ALIVE
        @classmethod
        def from_bytes(cls, _bytes: bytes):
            return cls()


    @auto_repr    
    class Info(Base):
        MESSAGE_TYPE_BYTE = MessageTypeByte.Client.INFO
        def __init__(self, name:str, sensor_count:int, unix_time_at_zero:int) -> None:
            self.name = name
            self.sensor_count = sensor_count
            self.unix_time_at_zero = unix_time_at_zero

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


    @auto_repr
    class SensorSamples(Base):
        MESSAGE_TYPE_BYTE = MessageTypeByte.Client.SENSOR_SAMPLES
        def __init__(self, sensor_id:int, samples:tuple[Sample, ...]) -> None:
            self.sensor_id = sensor_id
            self.samples = samples

        @classmethod
        def from_bytes(cls, _bytes:bytes):
            i = 1
            sensor_id:int = _bytes[i]
            i += 1
            sample_count:int = _bytes[i]
            i += 1
            if len(_bytes) < i + sample_count*Sample.SIZE:
                raise Exception('SensorSample message is not complete')
            samples:tuple[Sample, ...] = tuple(Sample.from_bytes(_bytes[j:j+Sample.SIZE]) for j in range(i, i+sample_count*Sample.SIZE, Sample.SIZE))
            return cls(sensor_id, samples)


    class ACK(Base):
        MESSAGE_TYPE_BYTE = MessageTypeByte.Client.ACK
        def __init__(self, sensor_id:int) -> None:
            self.sensor_id = sensor_id
        
        @classmethod
        def from_bytes(cls, _bytes: bytes):
            return cls(_bytes[1])
        


    @classmethod
    def from_bytes(cls, _bytes:bytes) -> Base|None:
        for subcls in cls.Base.__subclasses__():
            if subcls.MESSAGE_TYPE_BYTE == _bytes[0]:
                return subcls.from_bytes(_bytes)
        return None


