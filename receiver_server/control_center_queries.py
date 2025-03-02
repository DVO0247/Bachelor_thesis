"""
This module provides connection to the control center database and query functions.
"""

import os
import django
from django.db.models import Max
import sys
from pathlib import Path
from dataclasses import dataclass
from tcp_sensor_node_protocol import SensorParams
import logging
log = logging.getLogger(__name__)

django_root_path = Path(__file__).parent.parent/'django_web'
sys.path.append(str(django_root_path))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from control_center.models import SensorNodeTypes, Sensor, SensorNode, Measurement

DATA_DIR_PATH = Path(__file__).parent.parent/'data'

@dataclass
class NamedSensorParams(SensorParams):
    name:str

def create_sensor_node(name:str, type:SensorNodeTypes, sensor_count:int|None) -> SensorNode:
    sensor_node = SensorNode(name=name, type=type)
    if sensor_node.manage_sensors and not sensor_count:
        raise Exception(f'Sensor count needed for {type.name} type')
    sensor_node.full_clean()
    sensor_node.save()
    if sensor_node.manage_sensors:
        for i in range(sensor_count): # type: ignore
            sensor = Sensor(sensor_node=sensor_node, id_in_sensor_node=i)
            sensor.save()
    log.info(f'Sensor node {name} created')
    return sensor_node
    

def get_sensor_node_id_or_create(name:str, type:SensorNodeTypes, sensor_count:int|None = None) -> int:
    """Create a new sensor node if it doesn't exist and retrieve the sensor node ID."""
    sensor_node = SensorNode.objects.filter(name=name).first()
    if sensor_node:
        if sensor_node.manage_sensors and sensor_count != Sensor.objects.filter(sensor_node=sensor_node).count():
            raise Exception(f'Control center has different number of sensors for {sensor_node}')
        return sensor_node.pk
    else:
        sensor_node = create_sensor_node(name, type, sensor_count)
        return sensor_node.pk


def get_running_project_measurements(sensor_node_id:int) -> list[tuple[str, int]]:
    """Retrieve the measurement IDs of all projects with running measurements for a specific sensor node."""
    measurements = Measurement.objects.filter(end_time=None, sensor_nodes=sensor_node_id)
    return [(m.project.name, m.id_in_project) for m in measurements]

def is_initialized(sensor_node_id:int) -> bool:
    sensor_node = SensorNode.objects.get(pk=sensor_node_id)
    return sensor_node.initialized

def get_params_for_sensors(sensor_node_id:int) -> list[NamedSensorParams]:
    sensors = Sensor.objects.filter(sensor_node__pk=sensor_node_id, sensor_node__initialized=True)
    return [NamedSensorParams(sensor.sample_period, sensor.samples_per_message, sensor.name) for sensor in sensors] # type: ignore

def get_sensor_names(sensor_node_id:int) -> list[str]:
    sensors = Sensor.objects.filter(sensor_node=sensor_node_id)
    return [sensor.name for sensor in sensors if sensor.name]

def add_sensor(sensor_node_id:int, sensor_name:str) -> Sensor:
    """Add a new sensor to the Control Center database.

    This function is designed to add a sensor to the system for sensor nodes that do not have their sensors managed
    within the Control Center.
    """
    sensor_node = SensorNode.objects.get(pk=sensor_node_id)
    max_id = Sensor.objects.filter(sensor_node=sensor_node).aggregate(Max('id_in_sensor_node'))['id_in_sensor_node__max']

    sensor = Sensor(
        sensor_node = sensor_node,
        id_in_sensor_node = max_id + 1 if max_id is not None else 0,
        name = sensor_name
    )
    #sensor.full_clean()
    sensor.save()
    log.info(f'Sensor {sensor.name} added to {sensor_node.name}')
    return sensor

def set_sensor_node_conn_state(sensor_node_id:int, state:bool):
    """Set connection state for the sensor node"""
    sensor_node = SensorNode.objects.get(pk=sensor_node_id)
    sensor_node.connected = state
    sensor_node.save()

def set_all_sensor_nodes_conn_state(state:bool):
    """Set connection state for all sensor nodes"""
    for sensor_node in SensorNode.objects.all():
        sensor_node.connected = state
        sensor_node.save()

if __name__ == '__main__':
    pass
