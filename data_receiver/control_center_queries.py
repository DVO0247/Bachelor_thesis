import os
import django
import sys
from pathlib import Path

django_root_path = Path(__file__).parent.parent/'django_web'
sys.path.append(str(django_root_path))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from control_center.models import SensorNodeTypes, Sensor, SensorNode, Project, get_measurement_dir_path

DATA_DIR_PATH = Path(__file__).parent.parent/'data'

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
            sensor = Sensor(sensor_node=sensor_node, internal_id=i)
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


def get_paths_for_sensor(sensor_node_id:int, sensor_id:int) -> tuple[Path, ...]:
    sensor = Sensor.objects.filter(sensor_node__pk=sensor_node_id, internal_id=sensor_id).first()
    if sensor:
        projects = Project.objects.filter(sensor_nodes=sensor.sensor_node, running=True)
        paths = tuple(get_measurement_dir_path(DATA_DIR_PATH, sensor, project) for project in projects)
        return paths
    else:
        raise Exception(f'Sensor {sensor_node_id} {sensor_id} not found')

def get_init_state(sensor_node_id:int) -> bool|None:
    sensor_node = SensorNode.objects.filter(pk=sensor_node_id).first()
    return sensor_node.initialized if sensor_node else None
    
def get_params_for_sensors(sensor_node_id:int) -> tuple[tuple[int, int], ...]|None:
    sensors = Sensor.objects.filter(sensor_node__pk=sensor_node_id, sensor_node__initialized=True)
    if sensors:
        return tuple((sensor.sample_period, sensor.samples_per_packet) for sensor in sensors) # type: ignore
    else:
        return None
        

if __name__ == '__main__':
    pass

# TODO: LOG file with only once warnings