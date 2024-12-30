from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_delete
from django.core.validators import MaxValueValidator, MinValueValidator
import os
from enum import Enum
from control_center.utils.init_dbs import new_measurement_db
from django.db import connection
from datetime import datetime
from pathlib import Path

from django.db import models
from datetime import datetime

import re
from django.core.exceptions import ValidationError

NEW_DATA_DB_PATH = Path.cwd().parent/'data' # relative to Django root

class SensorNodeTypes(models.IntegerChoices):
    ESP32 = 0, 'ESP32'
    FBGUARD = 1, 'FBGuard'

class User(AbstractUser):
    active_project = models
    current_project = models.ForeignKey('Project', null=True, blank=True, on_delete=models.SET_NULL, related_name='users_with_this_project')
    darkmode = models.BooleanField(default=True)

class Project(models.Model):
    name = models.CharField(max_length=32, null=False, blank= False)
    description = models.TextField(max_length=400, null=True, blank=True)
    sensor_nodes = models.ManyToManyField('SensorNode')
    measurement_id = models.IntegerField(default=1,blank=True)
    measurement_start_datetime = models.DateTimeField(blank=True, null=True) # or CharField (?)
    running = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.pk}, {self.name}'

    def new_measurement(self)->None:
        self.running = True
        self.measurement_start_datetime = datetime.now()
        # get all sensor dir paths in this project  
        for sensor in Sensor.objects.filter(sensor_node__in=self.sensor_nodes.all()):
            measurement_path = get_measurement_dir_path(NEW_DATA_DB_PATH,sensor, self)
            print('Path:',measurement_path)
            print(self.measurement_start_datetime)

            os.makedirs(measurement_path.parent, exist_ok=True)
            new_measurement_db(measurement_path)
            sensor.save()

        # DEBUG
        print('queries:')
        for query in connection.queries:
            print(query['sql'])
    
class SensorNode(models.Model):
    name = models.CharField(max_length=32, null=True, blank=True, unique=True)
    initialized = models.BooleanField(default=False)
    type = models.IntegerField(choices=SensorNodeTypes) # type: ignore

    def __str__(self) -> str:
        return f'{self.pk}, {self.name}'

class Sensor(models.Model):
    sensor_node = models.ForeignKey(SensorNode, related_name='sensors', on_delete=models.CASCADE)
    internal_id = models.PositiveIntegerField(null=False, blank=False)
    name = models.CharField(max_length=32, null=True, blank=False)
    sample_period = models.PositiveIntegerField(null=True, blank=False)
    samples_per_packet = models.PositiveIntegerField(null=True, blank=False) # TODO: add validators

    class Meta:
        unique_together = ['sensor_node', 'internal_id']

    def save(self, *args, **kwargs):
        samples_per_packet_range = (1,121)
        if self.samples_per_packet:
            if self.samples_per_packet < samples_per_packet_range[0]:
                self.samples_per_packet = samples_per_packet_range[0]
            elif self.samples_per_packet > samples_per_packet_range[1]:
                self.samples_per_packet = samples_per_packet_range[1]
                
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.sensor_node.name}, {self.internal_id}, {self.name}'

class UserProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    is_owner = models.BooleanField()
    #is_editor = models.BooleanField(null=True, blank=True)
    
    class Meta:
        unique_together = (('user','project'),)

    def __str__(self) -> str:
        return f'{self.pk}, {self.user.get_full_name()}, ({self.project})'
    
'''
# TODO:change to M:N field
class ProjectSensorNode(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    sensor_node = models.ForeignKey(SensorNode, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('sensor_node', 'project'),)
'''

'''
def get_sensor_dir_path(sensor:Sensor, project:Project) -> Path:
    return Path(f'{NEW_DATA_DB_PATH}/{project.pk}_{project.name}/{sensor.sensor_node.pk}_{sensor.sensor_node.name}/{sensor.internal_id}_{sensor.name}/')
'''

'''
def get_sensor_dir_path(sensor:Sensor, project:Project) -> Path:
    return NEW_DATA_DB_PATH/f'{project.pk}_{project.name}'/f'{sensor.sensor_node.pk}_{sensor.sensor_node.name}'/f'{sensor.internal_id}_{sensor.name}'
'''

def get_measurement_dir_path(data_dir_path:Path, sensor:Sensor, project:Project) -> Path:
    measurement_start_str = convert_datetime_for_path(project.measurement_start_datetime) if project.measurement_start_datetime else None
    return data_dir_path/f'{project.pk}_{project.name}'/f'{sensor.sensor_node.pk}_{sensor.sensor_node.name}'/f'{sensor.internal_id}_{sensor.name}'/f'{project.measurement_id}_{measurement_start_str}.db'

def convert_datetime_for_path(_datetime:datetime)->str:
    return _datetime.strftime("%Y-%m-%dT%H-%M-%S")
