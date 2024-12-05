import struct

START_OF_SAMPLES_BYTE = 0x02
END_OF_SAMPLES_BYTE = 0x03
SPECIAL_IDENTIFIER_BYTE = 0xFF
ACK_BYTE = 0x06

ENC = 'ascii'
MAX_SAMPLES_PER_PACKET = 121
INFO_REQUEST_MESSAGE = bytes(6)

def get_change_params_message(sensor_id:int, sample_period_s:float, samples_per_packet:int):
    if samples_per_packet > MAX_SAMPLES_PER_PACKET:
        raise Exception(F'Max samples per packet is {MAX_SAMPLES_PER_PACKET}')
    else:
        return sensor_id.to_bytes(1, byteorder='little') + struct.pack('<f', sample_period_s) + samples_per_packet.to_bytes(1, byteorder='little')

class Sample:
    SIZE = 12
    def __init__(self, timestamp:int, value:float) -> None:
        self.timestamp = timestamp
        self.value = value

    @classmethod
    def from_bytes(cls, sample_bytes:bytes):
        timestamp:int = int.from_bytes(sample_bytes[0:4], byteorder='little')
        value:float = struct.unpack('<d', sample_bytes[4:12])[0]
        return cls(timestamp, value)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.__dict__})'

class Samples:
    def __init__(self, sensor_id:int, samples:tuple[Sample, ...]) -> None:
        self.sensor_id = sensor_id
        self.samples = samples

    @classmethod
    def from_bytes(cls, samples_bytes:bytes):
        if not Samples.is_complete(samples_bytes):
            ...
        start_of_samples_i = 2
        end_of_samples_i = len(samples_bytes) - 1
        sensor_id:int = samples_bytes[0]
        samples:tuple[Sample, ...] = tuple(Sample.from_bytes(samples_bytes[i:i+Sample.SIZE]) for i in range(start_of_samples_i, end_of_samples_i, Sample.SIZE))
        return cls(sensor_id, samples)
    
    @staticmethod
    def is_complete(samples_bytes:bytes):
        if samples_bytes[1] != START_OF_SAMPLES_BYTE:
            raise Exception('message not start with START_OF_SAMPLES_BYTE')
            return False
        if samples_bytes[-1] != END_OF_SAMPLES_BYTE:
            raise Exception('message not start with END_OF_SAMPLES_BYTE')
            return False
        return True
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.__dict__})'
    
class Info:
    def __init__(self, name:str, sensor_count:int) -> None:
        self.name = name
        self.sensor_count = sensor_count

    @classmethod
    def from_bytes(cls, info_bytes:bytes):
        name = info_bytes[1:-1].decode(ENC)
        sensor_count = info_bytes[-1]
        return cls(name, sensor_count)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.__dict__})'

class ACK:
    pass
    
def get_message_from_bytes(message_bytes:bytes) -> ACK|Info|Samples:
    if message_bytes[0] == SPECIAL_IDENTIFIER_BYTE:
        if message_bytes[1] == ACK_BYTE and len(message_bytes) == 2:
            return ACK()
        else:
            return Info.from_bytes(message_bytes)
    else:
        return Samples.from_bytes(message_bytes)
