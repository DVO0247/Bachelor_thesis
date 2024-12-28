import os
import django
import sys
from pathlib import Path

django_root_path = os.path.join(os.path.dirname(__file__), '..', 'django_web')
sys.path.append(django_root_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from control_center.models import Sensor, SensorNode, Project, convert_datetime_for_path

SENSOR_DATA_PATH = r'../data'

def create_sensor_node(name:str, sensor_count:int) -> None:
    sensor_node = SensorNode(name=name)
    try:
        sensor_node.full_clean()
    except django.core.exceptions.ValidationError as e: # type: ignore
        print(f"Error: {e}")
        return
    else:
        sensor_node.save()
    
    for i in range(sensor_count):
        sensor = Sensor(sensor_node=sensor_node, internal_id=i)
        sensor.save()

def get_paths_for_sensor(sensor_node_name:str, sensor_id:int) -> tuple[Path, ...]:
    result = Project.objects.filter(
        running=True,
        projectsensornode__sensor_node__name=sensor_node_name,
        projectsensornode__sensor_node__sensors__internal_id=sensor_id
    ).values(
        'id', 'name', 
        'projectsensornode__sensor_node__id', 'projectsensornode__sensor_node__name',
        'projectsensornode__sensor_node__sensors__internal_id', 'projectsensornode__sensor_node__sensors__name',
        'measurement_id', 'measurement_start_datetime'
    )
    
    paths = tuple(Path(f'{SENSOR_DATA_PATH}/{r['id']}_{r['name']}/{r['projectsensornode__sensor_node__id']}_{r['projectsensornode__sensor_node__name']}/{r['projectsensornode__sensor_node__sensors__internal_id']}_{r['projectsensornode__sensor_node__sensors__name']}/{r['measurement_id']}_{convert_datetime_for_path(r['measurement_start_datetime'])}.sqlite3') for r in result)
    return paths

def is_initialized(sensor_node_name:str, sensor_count:int) -> bool:
    try:
        sensor_node = SensorNode.objects.get(name=sensor_node_name)
    except SensorNode.DoesNotExist:
        create_sensor_node(sensor_node_name, sensor_count)
        return False
    else:
        if sensor_node.initialized == 1:
            return True
        else:
            return False
    

if __name__ == '__main__':
    pass

