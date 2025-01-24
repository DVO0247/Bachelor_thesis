import os
import django
import sys
from pathlib import Path
from dataclasses import dataclass
from tcp_sensor_node_protocol import SensorParams

django_root_path = Path(__file__).parent.parent/'django_web'
sys.path.append(str(django_root_path))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from control_center.models import SensorNodeTypes, Sensor, SensorNode, Measurement, Project

DATA_DIR_PATH = Path(__file__).parent.parent/'data'

@dataclass
class NamedSensorParams(SensorParams):
    name:str

def create_sensor_node(name:str, sensor_count:int) -> SensorNode|None:
    sensor_node = SensorNode(name=name, type=SensorNodeTypes.ESP32)
    try:
        sensor_node.full_clean()
    except django.core.exceptions.ValidationError as e: # type: ignore
        print(f"Error: {e}")
        return None
    else:
        sensor_node.save()
        for i in range(sensor_count):
            sensor = Sensor(sensor_node=sensor_node, id_in_sensor_node=i)
            sensor.save()
        print(name, 'created')
        return sensor_node
    

def get_sensor_node_id_or_create(sensor_node_name:str, sensor_count:int) -> int|None:
    sensor_node = SensorNode.objects.filter(name=sensor_node_name).first()
    if sensor_node:
        if sensor_count != Sensor.objects.filter(sensor_node=sensor_node).count():
            raise Exception(f'DB has different number of sensors for {sensor_node}')
        return sensor_node.pk
    else:
        sensor_node = create_sensor_node(sensor_node_name, sensor_count)
        return sensor_node.pk if sensor_node else None


def get_running_projects(sensor_node_id:int) -> dict[str, int]:
    measurements = Measurement.objects.filter(end_time=None, sensor_nodes=sensor_node_id)
    projects = {m.project.name: m.id_in_project for m in measurements}
    return projects

def get_init_state(sensor_node_id:int) -> bool|None:
    sensor_node = SensorNode.objects.filter(pk=sensor_node_id).first()
    return sensor_node.initialized if sensor_node else None
    
def get_params_for_sensors(sensor_node_id:int) -> list[NamedSensorParams]:
    sensors = Sensor.objects.filter(sensor_node__pk=sensor_node_id, sensor_node__initialized=True)
    return [NamedSensorParams(sensor.sample_period, sensor.samples_per_packet, sensor.name) for sensor in sensors] # type: ignore
        

if __name__ == '__main__':
    pass

# TODO: LOG file with only once warnings