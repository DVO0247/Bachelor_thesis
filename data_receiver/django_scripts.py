import os
import django
import sys

django_root_path = os.path.join(os.path.dirname(__file__), '..', 'django_web')
sys.path.append(django_root_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from control_center.models import Sensor, SensorNode, Project

def create_sensor_node(name, sensor_count):
    sensor_node = SensorNode(name=name)
    try:
        sensor_node.full_clean()
        sensor_node.save()
    except django.core.exceptions.ValidationError as e:
        print(f"Error: {e}")
    
    for i in range(sensor_count):
        sensor = Sensor(sensor_node=sensor_node, internal_id=i)
        sensor.save()

def get():
    ...

if __name__ == '__main__':
    name = 'ESP1'
    sensor_id = 1
    sensor_node = SensorNode.objects.filter(name=name)
    sensor = Sensor.objects.filter(sensor_node=sensor_node, internal_id=sensor_id)
    project = Project.objects.filter(sensor_node)
