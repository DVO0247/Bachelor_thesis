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
    name = models.TextField(max_length=32, null=False, blank= False)
    description = models.TextField(max_length=400, null=False, blank= False)
    current_measurement = models.ForeignKey('Measurement', null=True, on_delete=models.SET_NULL, related_name='projects_with_this_measurement')

class Measurement(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.project.current_measurement = self
        dir_paths = []
        for node in SensorNode.objects.filter(project=self.project):
            for sensor in Sensor.objects.filter(sensor_node=node):
                dir_paths.append(get_db_dir_path(sensor))
        print('dir_paths:\n',dir_paths)
        for dir_path in dir_paths:
            new_measurement_db(f'{dir_path}{self.pk}.sqlite3')
        #os.makedirs(dir_paths)  
    
class SensorNode(models.Model):
    name = models.TextField(max_length=32, null=True, blank=True)
    project = models.ForeignKey(Project, null=True, on_delete=models.SET_NULL)

class Sensor(models.Model):
    name = models.TextField(max_length=32, null=False, blank= False)
    sensor_node = models.ForeignKey(SensorNode, related_name='sensors', on_delete=models.CASCADE)
    fvz = models.PositiveIntegerField()
    current_db_file_path = models.FileField(null=True, blank=True)

    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        #dir_path = f'{NEW_SN_DB_PATH}\\{self.sensor_node.project.pk}_{self.sensor_node.project.name}\\{self.sensor_node.pk}_{self.sensor_node.name}\\{self.pk}_{self.name}\\'
        dir_path = get_db_dir_path(self)
        print(dir_path)
        os.makedirs(dir_path)        

        #super().save(*args, **kwargs)

class UserProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    is_owner = models.BooleanField()
    #is_admin = models.BooleanField()
    
    class Meta:
        unique_together = (('user','project'),)

def get_db_dir_path(obj:Sensor) -> str:
    return f'{NEW_SN_DB_PATH}\\{obj.sensor_node.project.pk}_{obj.sensor_node.project.name}\\{obj.sensor_node.pk}_{obj.sensor_node.name}\\{obj.pk}_{obj.name}\\'