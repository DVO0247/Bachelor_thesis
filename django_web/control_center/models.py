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


class Project(models.Model):
    name = models.CharField(max_length=32, null=False, blank= False)
    description = models.TextField(max_length=400, null=True, blank=True)
    current_measurement = models.ForeignKey('Measurement', null=True, blank=True, on_delete=models.SET_NULL, related_name='projects_with_this_measurement')

    '''def get_current_measurement(self):
        return Measurement.objects.filter(project=self).order_by('-id').first()'''

    def __str__(self) -> str:
        return f'{self.pk}, {self.name}'

class Measurement(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='measurements')

    def __str__(self) -> str:
        return f'{self.pk}, ({self.project})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.project.current_measurement = self
        
        # get all sensor dir paths in this project
        file_paths = []   
        for sensor in Sensor.objects.filter(sensor_node__project=self.project).select_related('sensor_node', 'sensor_node__project'):
            file_path = f'{get_db_dir_path(sensor)}{self.pk}.sqlite3'
            sensor.current_db_file_path = os.path.abspath(file_path)
            sensor.save()
            file_paths.append(file_path)
        
        print('dir_paths:\n',file_paths)
        for file_path in file_paths:
            new_measurement_db(f'{file_path}')
        #os.makedirs(dir_paths)
    
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
        dir_path = get_db_dir_path(self)
        print(dir_path)
        os.makedirs(dir_path,exist_ok=True)

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

def get_db_dir_path(sensor:Sensor) -> str:
    return f'{NEW_DATA_DB_PATH}\\{sensor.sensor_node.project.pk}_{sensor.sensor_node.project.name}\\{sensor.sensor_node.pk}_{sensor.sensor_node.name}\\{sensor.pk}_{sensor.name}\\'
