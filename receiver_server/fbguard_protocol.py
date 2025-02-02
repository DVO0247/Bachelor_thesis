import struct
from dataclasses import dataclass
from typing import ClassVar, Self, Any

ENC = 'utf-8'
BYTE_ORDER = 'little'
DOUBLE_FORMAT = '<d'

@dataclass
class Header:
    sync:bytes # 3B
    packet_type:int # 1B
    device_id:str # 32B #null-terminated
    sensor_id:str # 32B #null-terminated
    packet_counter:int # 2B
    packet_readout_count:int # 2B
    packet_byte_size:int|None = None # 4B
    header_checksum:Any = None # 4B

    EXPECTED_SYNC:ClassVar = b'\x55\x00\x55'

    def __post_init__(self):
        if self.sync != self.EXPECTED_SYNC:
            raise Exception('Wrong sync bytes')
        self.packet_byte_size = self.packet_byte_size if self.packet_byte_size else 80 + self.packet_readout_count*24 + 4
        
    @classmethod
    def from_bytes(cls, header_bytes:bytes):
        sync:bytes = header_bytes[0:3]
        if sync != cls.EXPECTED_SYNC:
            raise Exception(f'sync != {cls.EXPECTED_SYNC}')
        packet_type:int = header_bytes[3]
        device_id:str = bytes(header_bytes[4:36]).rstrip(b'\x00').decode(ENC)
        sensor_id:str = bytes(header_bytes[36:68]).rstrip(b'\x00').decode(ENC)
        packet_counter:int = int.from_bytes(header_bytes[68:70], BYTE_ORDER)
        packet_readout_count:int = int.from_bytes(header_bytes[70:72], BYTE_ORDER)
        packet_byte_size:int|None = int.from_bytes(header_bytes[72:76], BYTE_ORDER)
        header_checksum = header_bytes[76:80] #TODO: checksum
        return cls(sync, packet_type, device_id, sensor_id, packet_counter, packet_readout_count, packet_byte_size, header_checksum)
        
    def to_bytes(self) -> bytes:
        device_id_bytes = self.device_id.encode(ENC)[:31].ljust(32, b'\x00')
        sensor_id_bytes = self.sensor_id.encode(ENC)[:31].ljust(32, b'\x00')
        return self.sync + self.packet_type.to_bytes(1, BYTE_ORDER) + device_id_bytes + sensor_id_bytes + self.packet_counter.to_bytes(2, BYTE_ORDER) + self.packet_readout_count.to_bytes(2, BYTE_ORDER) + self.packet_byte_size.to_bytes(4, BYTE_ORDER) + bytes(4)  # type: ignore # TODO: checksum


@dataclass
class Readout:
    timestamp_seconds:int # 8B
    timestamp_microseconds:int # 8B
    value:float # 8B

    SIZE:ClassVar = 24
        
    @classmethod
    def from_bytes(cls, readout_bytes:bytes):
        timestamp_seconds:int = int.from_bytes(readout_bytes[0:8], BYTE_ORDER)
        timestamp_microseconds:int = int.from_bytes(readout_bytes[8:16], BYTE_ORDER)
        value:float = struct.unpack(DOUBLE_FORMAT, readout_bytes[16:24])[0]
        return cls(timestamp_seconds, timestamp_microseconds, value)
        
    def to_bytes(self) -> bytes:
        return self.timestamp_seconds.to_bytes(8, BYTE_ORDER)+self.timestamp_microseconds.to_bytes(8, BYTE_ORDER)+struct.pack(DOUBLE_FORMAT, self.value)

        
@dataclass
class Data:
    readouts:list[Readout]
        
    @classmethod
    def from_bytes(cls, data_bytes:bytes):
        return cls([Readout.from_bytes(data_bytes[i:i+Readout.SIZE]) for i in range(0, len(data_bytes), Readout.SIZE)])
        
    def to_bytes(self) -> bytes:
        return b''.join(readout.to_bytes() for readout in self.readouts)


@dataclass
class Message:
    header:Header
    data:Data
    packet_checksum:bytes|None = None
    
    @classmethod
    def from_bytes(cls, message_bytes:bytes):
        index = 0
        header = Header.from_bytes(message_bytes[index:80])
        index += 80
        data_size = header.packet_readout_count*24
        data = Data.from_bytes(message_bytes[index:index+data_size])
        index += data_size
        packet_checksum = message_bytes[index:index+4]
        return cls(header, data, packet_checksum)
    
    @classmethod
    def from_bytes_with_remainder(cls, message_bytes:bytes) -> tuple[Self|None, bytes]:
        expected_size = cls.get_expected_size(message_bytes)
        if expected_size and expected_size <= len(message_bytes):
            return cls.from_bytes(message_bytes[:expected_size]), message_bytes[expected_size:]
        else:
            return None, message_bytes
    
    @classmethod
    def list_from_bytes_with_remainder(cls, message_bytes:bytes) -> tuple[list[Self], bytes] :
        cls_list: list[Self] = []
        bytes_view = memoryview(message_bytes)
        while (expected_size := cls.get_expected_size(bytes_view)) and expected_size <= len(bytes_view):
            cls_list.append(cls.from_bytes(bytes_view[:expected_size]))
            bytes_view = bytes_view[expected_size:]
        return cls_list, bytes(bytes_view)

    @classmethod
    def build(cls, device_id:str, sensor_id:str, packet_counter:int, readouts:list[Readout], calc_checksum=False):
        if calc_checksum:
            raise NotImplementedError
        if len(readouts) > 1024:
            raise Exception('maximum number of readouts exceeded')
        header = Header(Header.EXPECTED_SYNC, 0, device_id, sensor_id, packet_counter, len(readouts), None, None)
        data = Data(readouts)
        return cls(header, data, None) #TODO: checksum

    def to_bytes(self) -> bytes:
        return self.header.to_bytes() + self.data.to_bytes() + bytes(4) #TODO: checksum
    
    # returns expected size of whole message if can, else returns None
    @staticmethod
    def get_expected_size(message_bytes:bytes) -> int | None: 
        if len(message_bytes) < 76:
            return None
        else:
            return int.from_bytes(message_bytes[72:76], BYTE_ORDER)
