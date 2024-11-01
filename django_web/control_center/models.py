from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_delete
import os
from control_center.utils.init_dbs import new_measurement_db

NEW_SN_DB_PATH = '..\\data' # relative to Django root

class User(AbstractUser):
    pass
    #test_field = models.IntegerField(default=0) # for test

class Project(models.Model):
    name = models.CharField(max_length=32, null=False, blank= False)
    description = models.TextField(max_length=400, null=True, blank=True)
    current_measurement = models.ForeignKey('Measurement', null=True, blank=True, on_delete=models.SET_NULL, related_name='projects_with_this_measurement')

    def __str__(self) -> str:
        return f'{self.pk}, {self.name}'

class Measurement(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f'{self.pk}, ({self.project})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.project.current_measurement = self
        file_paths = []
        # get all sensor dir paths in this project
        for node in SensorNode.objects.filter(project=self.project):
            for sensor in Sensor.objects.filter(sensor_node=node):
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
        #dir_path = f'{NEW_SN_DB_PATH}\\{self.sensor_node.project.pk}_{self.sensor_node.project.name}\\{self.sensor_node.pk}_{self.sensor_node.name}\\{self.pk}_{self.name}\\'
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

def get_db_dir_path(obj:Sensor) -> str:
    return f'{NEW_SN_DB_PATH}\\{obj.sensor_node.project.pk}_{obj.sensor_node.project.name}\\{obj.sensor_node.pk}_{obj.sensor_node.name}\\{obj.pk}_{obj.name}\\'