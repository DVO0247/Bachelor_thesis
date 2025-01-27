from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import connection
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import UserManager, BaseUserManager
from django.contrib.auth.hashers import make_password

from pathlib import Path
from datetime import datetime
from functools import cache
from collections import defaultdict

from api_clients import influxdb, grafana

class SensorNodeTypes(models.IntegerChoices):
    ESP32 = 0, 'ESP32'
    FBGUARD = 1, 'FBGuard'

class CustomUserManager(UserManager):
    pass

class User(AbstractUser):
    darkmode = models.BooleanField(default=True)

    def save(self, *args, **kwargs) -> None:
        grafana.change_user_role(self.username, 'Admin' if self.is_staff else 'Editor')
        return super().save(*args, **kwargs)

    def set_password(self, raw_password):
        if raw_password:
            if not self.pk:
                grafana.create_user(self.username, raw_password, 'Editor')
            else:
                grafana.change_password(self.username, raw_password)

        return super().set_password(raw_password)

    def __str__(self):
        return self.username

class Project(models.Model):
    name = models.CharField(max_length=32, null=False, blank= False)
    description = models.TextField(max_length=400, null=True, blank=True)
    sensor_nodes = models.ManyToManyField('SensorNode')
    users = models.ManyToManyField(User, through='UserProject')

    def get_last_measurement(self):
        return Measurement.objects.filter(project=self).last()

    def is_running(self):
        last_measurement = self.get_last_measurement()
        return last_measurement.is_running() if (last_measurement is not None) else False

    def save(self, *args, **kwargs):
        self.name = clean_name(self.name)

        if not self.pk:
            influxdb.create_bucket(self.name)
            grafana.create_team(self.name)
        else:
            current = Project.objects.get(pk=self.pk)
            if current.name!=self.name:
                influxdb.rename_bucket(current.name, self.name)

        # TODO: grafana change querry bucket name (?)
        super().save(*args, **kwargs)
        
            
    def __str__(self) -> str:
        return f'{self.pk}, {self.name}'

    def start_measurement(self)->None:
        last_measurement = self.get_last_measurement()
        if last_measurement and last_measurement.is_running():
            self.stop_measurement()
        measurement = Measurement.objects.create(project=self,
                                  id_in_project=last_measurement.id_in_project+1 if last_measurement is not None else 0,
                                  )
        
        measurement.sensor_nodes.set(self.sensor_nodes.all())
        measurement.save()

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

    def __str__(self) -> str:
        return f'{self.project.pk}, {self.id_in_project}'

class SensorNode(models.Model):
    name = models.CharField(max_length=32, unique=True)
    initialized = models.BooleanField(default=False)
    type = models.IntegerField(choices=SensorNodeTypes) # type: ignore

    def is_running(self):
        projects = Project.objects.filter(sensor_nodes=self)
        for project in projects:
            if project.is_running():
                return True
        return False

    def save(self, *args, **kwargs):
        self.name = clean_name(self.name)
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
            self.name = clean_name(self.name)
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
        if not self.pk and not self.is_owner:
            grafana.add_team_member(self.project.name, self.user.username)
        super().save(*args, **kwargs)
        

    def __str__(self) -> str:
        return f'{self.pk}, {self.user}, ({self.project})'

'''
def update_grafana_team_members(project:Project):
    team_members:grafana.TeamMembers = defaultdict(list)
    for user_project in UserProject.objects.filter(project=project):
        print('user_project:', user_project.user.username)
        team_members['admins' if user_project.is_editor else 'members'].append(user_project.user.username)
    grafana.update_team_members(project.name, team_members)
'''

@receiver(pre_delete, sender=UserProject,)
def delete_grafana_team_member(sender, instance:UserProject, **kwargs):
    grafana.remove_team_member(instance.project.name, instance.user.username)
    #update_grafana_team_members(instance.project)

@receiver(pre_delete, sender=Project)
def project_pre_delete(sender, instance:Project, **kwargs):
    influxdb.delete_bucket(instance.name)
    grafana.delete_team(instance.name)

def clean_name(name:str) -> str:
    return name.replace('"', '')