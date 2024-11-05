from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_delete
import os
from control_center.utils.init_dbs import new_measurement_db
from django.db import connection

NEW_DATA_DB_PATH = '..\\data' # relative to Django root

class User(AbstractUser):
    active_project = models
    current_project = models.ForeignKey('Project', null=True, blank=True, on_delete=models.SET_NULL, related_name='users_with_this_project')
    darkmode = models.BooleanField(default=True)


class Project(models.Model):
    name = models.CharField(max_length=32, null=False, blank= False)
    description = models.TextField(max_length=400, null=True, blank=True)
    measurement_id = models.IntegerField(default=1,blank=True)
    running = models.BooleanField(default=False)
    
    '''def get_current_measurement(self):
        return Measurement.objects.filter(project=self).order_by('-id').first()'''

    def __str__(self) -> str:
        return f'{self.pk}, {self.name}'
    
    def new_measurement(self)->None:
        self.running = True
        # get all sensor dir paths in this project  
        for sensor in Sensor.objects.filter(sensor_node__project=self).select_related('sensor_node', 'sensor_node__project'):
            sensor_dir_path = get_sensor_db_dir_path(sensor)
            file_path = f'{sensor_dir_path}{self.measurement_id}.sqlite3'

            os.makedirs(sensor_dir_path,exist_ok=True)
            new_measurement_db(f'{file_path}')
            sensor.current_db_file_path = os.path.abspath(file_path)
            sensor.save()
        print('queries:')
        for query in connection.queries:
            print(query['sql'])
    
class SensorNode(models.Model):
    name = models.CharField(max_length=32, null=True, blank=True)
    project = models.ForeignKey(Project, null=True, on_delete=models.SET_NULL)

    def __str__(self) -> str:
        return f'{self.pk}, {self.name}'

class Sensor(models.Model):
    name = models.CharField(max_length=32, null=False, blank= False)
    sensor_node = models.ForeignKey(SensorNode, related_name='sensors', on_delete=models.CASCADE)
    fvz = models.PositiveIntegerField(blank=True, null=True)
    current_db_file_path = models.CharField(max_length=4096, null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.pk}, {self.sensor_node.name}, {self.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        '''dir_path = get_sensor_db_dir_path(self)
        print(dir_path)
        os.makedirs(dir_path,exist_ok=True)'''

        #super().save(*args, **kwargs)

class UserProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    is_owner = models.BooleanField()
    #is_admin = models.BooleanField()
    
    class Meta:
        unique_together = (('user','project'),)

    def __str__(self) -> str:
        return f'{self.pk}, {self.user.get_full_name()}, ({self.project})'

def get_sensor_db_dir_path(sensor:Sensor) -> str:
    return f'{NEW_DATA_DB_PATH}\\{sensor.sensor_node.project.pk}_{sensor.sensor_node.project.name}\\{sensor.sensor_node.pk}_{sensor.sensor_node.name}\\{sensor.pk}_{sensor.name}\\'
