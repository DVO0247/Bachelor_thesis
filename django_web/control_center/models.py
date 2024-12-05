from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_delete
from django.core.validators import MaxValueValidator, MinValueValidator
import os
from control_center.utils.init_dbs import new_measurement_db
from django.db import connection
from datetime import datetime

from django.db import models
from datetime import datetime

NEW_DATA_DB_PATH = '..\\data' # relative to Django root

import re
from django.core.exceptions import ValidationError

class FormattedDateTimeField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 19  # Odpovídá délce formátu YYYY_MM_DD_hh_mm_ss
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        """
        Před uložením do databáze převede `datetime` na požadovaný řetězec.
        """
        print(f"get_prep_value called with: {value} (type: {type(value)})")
        if isinstance(value, datetime):
            return value.strftime('%Y_%m_%d_%H_%M_%S')
        return value

    def from_db_value(self, value, expression, connection):
        """
        Po načtení z databáze převede řetězec zpět na objekt `datetime`.
        """
        if value is None:
            return value
        return datetime.strptime(value, '%Y_%m_%d_%H_%M_%S')

    def to_python(self, value):
        """
        Při přístupu v Pythonu zajistí, že hodnota je vždy `datetime` nebo None.
        """
        if isinstance(value, datetime) or value is None:
            return value
        return datetime.strptime(value, '%Y_%m_%d_%H_%M_%S')

    def validate(self, value, model_instance):
        """
        Zkontroluje, zda hodnota odpovídá formátu YYYY_MM_DD_hh_mm_ss.
        """
        super().validate(value, model_instance)
        if value and not re.match(r'^\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}$', value):
            raise ValidationError(f"Hodnota '{value}' není ve správném formátu YYYY_MM_DD_hh_mm_ss.")

class User(AbstractUser):
    active_project = models
    current_project = models.ForeignKey('Project', null=True, blank=True, on_delete=models.SET_NULL, related_name='users_with_this_project')
    darkmode = models.BooleanField(default=True)

class Project(models.Model):
    name = models.CharField(max_length=32, null=False, blank= False)
    description = models.TextField(max_length=400, null=True, blank=True)
    measurement_id = models.IntegerField(default=1,blank=True)
    measurement_start_datetime = FormattedDateTimeField(blank=True, null=True) # or CharField (?)
    running = models.BooleanField(default=False)
    sensor_nodes = models.ManyToManyField('SensorNode')

    def __str__(self) -> str:
        return f'{self.pk}, {self.name}'
    
    def new_measurement(self)->None:
        self.running = True
        self.measurement_start_datetime = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        # get all sensor dir paths in this project  
        for sensor in Sensor.objects.filter(sensor_node__projectsensornode__project=self).select_related('sensor_node'):
            sensor_dir_path = get_sensor_dir_path(sensor, self)
            print(self.measurement_start_datetime)
            file_path = f'{sensor_dir_path}{self.measurement_id}__{self.measurement_start_datetime}.sqlite3'

            os.makedirs(sensor_dir_path,exist_ok=True)
            new_measurement_db(f'{file_path}')
            sensor.current_db_file_path = os.path.abspath(file_path)
            sensor.save()

        # DEBUG
        print('queries:')
        for query in connection.queries:
            print(query['sql'])
    
class SensorNode(models.Model):
    name = models.CharField(max_length=32, null=True, blank=True, unique=True)
    initialized = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.pk}, {self.name}'

class Sensor(models.Model):
    sensor_node = models.ForeignKey(SensorNode, related_name='sensors', on_delete=models.CASCADE)
    internal_id = models.PositiveIntegerField(null=False, blank=False)
    name = models.CharField(max_length=32, null=True, blank=True)
    sample_period = models.FloatField(blank=True, null=True)
    samples_per_packet = models.PositiveIntegerField(blank=True, null=True) # TODO: add validators

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
    #is_admin = models.BooleanField()
    
    class Meta:
        unique_together = (('user','project'),)

    def __str__(self) -> str:
        return f'{self.pk}, {self.user.get_full_name()}, ({self.project})'
    

# TODO:change to M:N field
class ProjectSensorNode(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    sensor_node = models.ForeignKey(SensorNode, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('sensor_node', 'project'),)    

def get_sensor_dir_path(sensor:Sensor, project:Project) -> str:
    return f'{NEW_DATA_DB_PATH}\\{project.pk}_{project.name}\\{sensor.sensor_node.pk}_{sensor.sensor_node.name}\\{sensor.pk}_{sensor.name}\\'
