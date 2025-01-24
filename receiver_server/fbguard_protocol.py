import struct
from dataclasses import dataclass
from typing import ClassVar

ENC = 'utf-8'
BYTE_ORDER = 'little'
DOUBLE_FORMAT = '<d'

class Header:
    EXPECTED_SYNC:ClassVar = b'\x55\x00\x55'
    
    def __init__(self, 
        sync:bytes|None, 
        packet_type:int|None,
        device_id:str,
        sensor_id:str,
        packet_counter:int,
        packet_readout_count:int,
        packet_byte_size:int|None = None,
        header_checksum = None
        ) -> None:
        self.sync = sync if sync else self.EXPECTED_SYNC #3
        self.packet_type = packet_type if packet_type else 0x00 #1
        self.device_id = device_id #32 #null-terminated
        self.sensor_id = sensor_id #32 #null-terminated
        self.packet_counter = packet_counter % 0x10000 #2
        self.packet_readout_count = packet_readout_count #2
        self.packet_byte_size = packet_byte_size if packet_byte_size else 80 + self.packet_readout_count*24 + 4 #4
        self.header_checksum = header_checksum #4
        
    @classmethod
    def from_bytes(cls, header_bytes:bytes):
        sync:bytes|None = header_bytes[0:3]
        if sync != cls.EXPECTED_SYNC:
            raise Exception(f'sync != {cls.EXPECTED_SYNC}')
        packet_type:int|None = header_bytes[3]
        device_id:str = header_bytes[4:36].rstrip(b'\x00').decode(ENC)
        sensor_id:str = header_bytes[36:68].rstrip(b'\x00').decode(ENC)
        packet_counter:int = int.from_bytes(header_bytes[68:70], BYTE_ORDER)
        packet_readout_count:int = int.from_bytes(header_bytes[70:72], BYTE_ORDER)
        packet_byte_size:int|None = int.from_bytes(header_bytes[72:76], BYTE_ORDER)
        header_checksum = header_bytes[76:80] #TODO: checksum
        return cls(sync, packet_type, device_id, sensor_id, packet_counter, packet_readout_count, packet_byte_size, header_checksum)
        
    def to_bytes(self) -> bytes:
        device_id_bytes = self.device_id.encode(ENC)[:31].ljust(32, b'\x00')
        sensor_id_bytes = self.sensor_id.encode(ENC)[:31].ljust(32, b'\x00')
        return self.sync + self.packet_type.to_bytes(1, BYTE_ORDER) + device_id_bytes + sensor_id_bytes + self.packet_counter.to_bytes(2, BYTE_ORDER) + self.packet_readout_count.to_bytes(2, BYTE_ORDER) + self.packet_byte_size.to_bytes(4, BYTE_ORDER) + bytes(4) #TODO: checksum
    
    def __repr__(self):
        return f'{self.__class__.__name__}({', '.join([f'{k}={v}' for k,v in self.__dict__.items()])})'


@dataclass
class Readout:
    timestamp_seconds:int #8
    timestamp_microseconds:int #8
    value:float #8

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
    readouts:tuple[Readout, ...]
        
    @classmethod
    def from_bytes(cls, data_bytes:bytes):
        return cls(tuple(Readout.from_bytes(data_bytes[i:i+Readout.SIZE]) for i in range(0, len(data_bytes), Readout.SIZE)))
        
    def to_bytes(self) -> bytes:
        return b''.join(readout.to_bytes() for readout in self.readouts)


@dataclass
class Message:
    header:Header
    data:Data
    packet_checksum:bytes|None = None
    
    @classmethod
    def from_bytes(cls, message_bytes:bytes):
        header = Header.from_bytes(message_bytes[0:80])
        data_size = header.packet_readout_count*24
        data_end = 80+data_size
        data = Data.from_bytes(message_bytes[80:data_end])
        packet_checksum = message_bytes[data_end:data_end+4]
        return cls(header, data, packet_checksum)

    @classmethod
    def build(cls, device_id:str, sensor_id:str, packet_counter:int, readouts:tuple[Readout, ...]):
        if len(readouts) > 1024:
            raise Exception('maximum number of readouts exceeded')
        header = Header(None, None, device_id, sensor_id, packet_counter, len(readouts), None, None)
        data = Data(readouts)
        return cls(header, data, None) #TODO: checksum

    def to_bytes(self) -> bytes:
        return self.header.to_bytes() + self.data.to_bytes() + bytes(4) #TODO: checksum
    
    # returns expected size of whole message if can else returns None
    @staticmethod
    def get_expected_size(message_bytes:bytes) -> int | None: 
        if len(message_bytes) < 76:
            return None
        else:
            return int.from_bytes(message_bytes[72:76], BYTE_ORDER)
