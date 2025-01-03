from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_delete
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
import os
import shutil
from control_center.utils.init_dbs import new_measurement_db
from django.db import connection
from datetime import datetime
from django.utils import timezone
from pathlib import Path
import re

NEW_DATA_DB_PATH = Path.cwd().parent/'data' # Path.cwd() = django root

FORBIDDEN_NAME_CHARS = '[\\/:"*?<>|]+'

class SensorNodeTypes(models.IntegerChoices):
    ESP32 = 0, 'ESP32'
    FBGUARD = 1, 'FBGuard'

class User(AbstractUser):
    darkmode = models.BooleanField(default=True)

class Project(models.Model):
    name = models.CharField(max_length=32, null=False, blank= False)
    description = models.TextField(max_length=400, null=True, blank=True)
    sensor_nodes = models.ManyToManyField('SensorNode')
    users = models.ManyToManyField(User, through='UserProject')
    path = models.CharField(max_length=4096, null=True)

    def get_last_measurement(self):
        return Measurement.objects.filter(project=self).last()

    def is_running(self):
        last_measurement = self.get_last_measurement()
        return last_measurement.is_running() if (last_measurement is not None) else False

    def get_path_name(self) -> str:
        return f'{self.pk}_{self.name}'

    def save(self, *args, **kwargs):
        self.name = re.sub(FORBIDDEN_NAME_CHARS, '_', self.name)

        if not self.pk:
            super().save(*args, **kwargs)
            self.path = str(NEW_DATA_DB_PATH/self.get_path_name())
        else:
            prev_obj = Project.objects.get(pk=self.pk)
            if prev_obj.name!=self.name:
                self.path = str(Path(prev_obj.path).parent/self.get_path_name()) # type: ignore
                print(prev_obj.path, self.path)
                if os.path.isdir(prev_obj.path): # type: ignore
                    shutil.move(prev_obj.path, self.path) # type: ignore
            
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.pk}, {self.name}'

    def start_measurement(self)->None:
        last_measurement = self.get_last_measurement()
        if last_measurement and last_measurement.end_time is None:
            self.stop_measurement()
        measurement = Measurement.objects.create(project=self,
                                  id_in_project=last_measurement.id_in_project+1 if last_measurement is not None else 0,
                                  )
        measurement.sensor_nodes.set(self.sensor_nodes.all())
        measurement.save()
        
        # get all sensor dir paths in this project  
        for sensor in Sensor.objects.filter(sensor_node__in=self.sensor_nodes.all()):
            measurement_path = measurement.get_dir_path(sensor)
            print('Path:',measurement_path)
            print(measurement.start_time)

            os.makedirs(measurement_path.parent, exist_ok=True)
            new_measurement_db(measurement_path)
            sensor.save()

        # DEBUG
        print('queries:')
        for query in connection.queries:
            print(query['sql'])

    def stop_measurement(self):
        last_measurement = self.get_last_measurement()
        if last_measurement:
            last_measurement.end_time = timezone.now()
            last_measurement.save()

class Measurement(models.Model):
    project = models.ForeignKey(Project, related_name='projects', on_delete=models.CASCADE)
    id_in_project = models.PositiveIntegerField()
    sensor_nodes = models.ManyToManyField('SensorNode', related_name='sensor_nodes')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['project', 'id_in_project']

    def get_next_or_running_id(self):
        return self.id_in_project+1 if not self.is_running() else self.id_in_project

    def is_running(self):
        return self.end_time is None

    def get_dir_path(self, sensor:'Sensor') -> Path:
        measurement_start_str = convert_datetime_for_path(self.start_time)
        return Path(self.project.path)/f'{sensor.sensor_node.pk}_{sensor.sensor_node.name}'/f'{sensor.id_in_sensor_node}_{sensor.name}'/f'{self.id_in_project}_{measurement_start_str}.db' # type: ignore

    def __str__(self) -> str:
        return f'{self.project.pk}, {self.id_in_project}'

class SensorNode(models.Model):
    name = models.CharField(max_length=32, unique=True)
    initialized = models.BooleanField(default=False)
    type = models.IntegerField(choices=SensorNodeTypes) # type: ignore

    def save(self, *args, **kwargs):
        self.name = re.sub(FORBIDDEN_NAME_CHARS, '_', self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.pk}, {self.name}'

class Sensor(models.Model):
    sensor_node = models.ForeignKey(SensorNode, related_name='sensors', on_delete=models.CASCADE)
    id_in_sensor_node = models.PositiveIntegerField(null=False, blank=False)
    name = models.CharField(max_length=32, null=True, blank=False)
    sample_period = models.PositiveIntegerField(null=True, blank=False)
    samples_per_packet = models.PositiveIntegerField(null=True, blank=False) # TODO: add validators

    class Meta:
        unique_together = ['sensor_node', 'id_in_sensor_node']

    def save(self, *args, **kwargs):
        if self.name:
            self.name = re.sub(FORBIDDEN_NAME_CHARS, '_', self.name)
        samples_per_packet_range = (1,121)
        if self.samples_per_packet:
            if self.samples_per_packet < samples_per_packet_range[0]:
                self.samples_per_packet = samples_per_packet_range[0]
            elif self.samples_per_packet > samples_per_packet_range[1]:
                self.samples_per_packet = samples_per_packet_range[1]
                
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.sensor_node.name}, {self.id_in_sensor_node}, {self.name}'

class UserProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    is_activated = models.BooleanField(default=True)
    is_owner = models.BooleanField(default=False)
    is_editor = models.BooleanField(default=False)
    
    
    class Meta:
        unique_together = (('user','project'),)

    def save(self, *args, **kwargs):
        if self.is_owner:
            self.is_editor = True
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.pk}, {self.user}, ({self.project})'
    
'''
def get_measurement_dir_path(project:Project, sensor:Sensor, measurement:Measurement|None = None) -> Path:
    if not measurement:
        measurement = project.get_last_measurement()
    measurement_start_str = convert_datetime_for_path(measurement.start_time) # type: ignore
    return Path(project.path)/f'{sensor.sensor_node.pk}_{sensor.sensor_node.name}'/f'{sensor.id_in_sensor_node}_{sensor.name}'/f'{measurement.id_in_project}_{measurement_start_str}.db' # type: ignore
'''

def convert_datetime_for_path(_datetime:datetime)->str:
    return _datetime.strftime("%Y-%m-%dT%H-%M-%S")
