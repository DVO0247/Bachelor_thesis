from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver

from api_clients import influxdb, grafana

# If set to True, automatically deletes the associated InfluxDB bucket and Grafana folder
# when a project is removed from the system.
PROJECT_AUTO_PURGE = True

class SensorNodeTypes(models.IntegerChoices):
    ESP32 = 0, 'ESP32'
    FBGUARD = 1, 'FBGuard'

# A tuple defining the sensor node types intended for sensor management.
SENSOR_NODES_FOR_SENSOR_MANAGE: tuple[SensorNodeTypes, ...] = (
    SensorNodeTypes.ESP32,
)

TEST_MEASUREMENT_ID = -1

class User(AbstractUser):
    darkmode = models.BooleanField(default=True)

    def save(self, *args, **kwargs) -> None:
        grafana.change_user_role(self.username, 'Admin' if self.is_staff else 'Editor')
        return super().save(*args, **kwargs)

    def set_password(self, raw_password):
        if raw_password:
            # Check if the object does not already exist
            if not self.pk:
                grafana.create_user(self.username, raw_password, 'Editor')
            else:
                grafana.change_user_password(self.username, raw_password)

        return super().set_password(raw_password)

    def __str__(self):
        return self.username


class Project(models.Model):
    name = models.CharField(max_length=32, null=False, blank= False)
    description = models.TextField(max_length=400, null=True, blank=True)
    sensor_nodes = models.ManyToManyField('SensorNode')
    users = models.ManyToManyField(User, through='UserProject')

    def get_last_measurement(self):
        return self.get_test_measurement() or Measurement.objects.filter(project=self).last()
    
    def get_test_measurement(self):
        return Measurement.objects.filter(project=self, id_in_project = TEST_MEASUREMENT_ID).first()

    def is_running(self):
        last_measurement = self.get_last_measurement()
        return last_measurement.is_running() if (last_measurement is not None) else False

    def save(self, *args, **kwargs):
        self.name = clean_name(self.name)

        # Check if the object does not already exist
        if not self.pk: 
            influxdb.create_bucket(self.name)
            grafana.create_folder(self.name)
            grafana.create_dashboard(self.name)
        else:
            # If the project already exists, check if the name has changed
            old = Project.objects.get(pk=self.pk)
            if old.name != self.name:
                # If the name has changed, rename the InfluxDB bucket and Grafana folder
                influxdb.rename_bucket(old.name, self.name)
                grafana.rename_folder(old.name, self.name)
        super().save(*args, **kwargs)
               
    def __str__(self) -> str:
        return f'{self.pk}, {self.name}'

    def start_measurement(self)->None:
        last_measurement = self.get_last_measurement()
        # Do nothing if the measurement is already running
        if last_measurement and last_measurement.is_running():
            return
        measurement = Measurement.objects.create(
            project = self,
            id_in_project = last_measurement.id_in_project+1 if last_measurement is not None else 0
        )
        
        measurement.sensor_nodes.set(self.sensor_nodes.all())
        measurement.save()
        influxdb.delete_test_measurement(self.name)

    def start_test_measurement(self)->None:
        # Do nothing if the measurement is already exists
        if not self.get_test_measurement():
            measurement = Measurement.objects.create(project = self, id_in_project = TEST_MEASUREMENT_ID)
            measurement.sensor_nodes.set(self.sensor_nodes.all())
            measurement.save()
        influxdb.delete_test_measurement(self.name)

    def stop_measurement(self):
        last_measurement = self.get_last_measurement()
        if last_measurement:
            if last_measurement.id_in_project == TEST_MEASUREMENT_ID:
                last_measurement.delete()
            else:
                last_measurement.end_time = timezone.now()
                last_measurement.save()

class Measurement(models.Model):
    project = models.ForeignKey(Project, related_name='projects', on_delete=models.CASCADE)
    id_in_project = models.IntegerField()
    sensor_nodes = models.ManyToManyField('SensorNode', related_name='sensor_nodes')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['project', 'id_in_project']

    def get_next_or_running_id(self):
        """
        Returns the next ID in the project if the current project is not running.
        If the project is running, returns the current project's ID.
        """
        return self.id_in_project + 1 if not self.is_running() else self.id_in_project

    def is_running(self):
        return self.end_time is None

    def __str__(self) -> str:
        return f'{self.project.pk}, {self.id_in_project}'

class SensorNode(models.Model):
    name = models.CharField(max_length=40, unique=True)
    initialized = models.BooleanField(default=False)
    type = models.IntegerField(choices=SensorNodeTypes) # type: ignore
    connected = models.BooleanField(default=False)

    @property
    def manage_sensors(self) -> bool:
        """
        Determines if the current `SensorNode` is included in the list of sensor types
        that are intended for sensor management.
        """
        return self.type in SENSOR_NODES_FOR_SENSOR_MANAGE

    def is_running(self):
        projects = Project.objects.filter(sensor_nodes=self)
        for project in projects:
            if project.is_running():
                return True
        return False

    def save(self, *args, **kwargs):
        self.name = clean_name(self.name)
        if not self.manage_sensors:
            self.initialized = True
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.pk}, {self.name}'


class Sensor(models.Model):
    sensor_node = models.ForeignKey(SensorNode, related_name='sensors', on_delete=models.CASCADE)
    id_in_sensor_node = models.PositiveIntegerField(null=False, blank=False)
    name = models.CharField(max_length=32, null=True, blank=False)
    sample_period = models.PositiveIntegerField(null=True, blank=False, verbose_name='Sample period (ms)')
    samples_per_message = models.PositiveIntegerField(null=True, blank=False) # TODO: add validators

    class Meta:
        unique_together = ['sensor_node', 'id_in_sensor_node']

    def save(self, *args, **kwargs):
        if self.name:
            self.name = clean_name(self.name)
        samples_per_message_range = (1,89)
        # Ensure `samples_per_message` is within the permitted range
        if self.samples_per_message:
            if self.samples_per_message < samples_per_message_range[0]:
                self.samples_per_message = samples_per_message_range[0]
            elif self.samples_per_message > samples_per_message_range[1]:
                self.samples_per_message = samples_per_message_range[1]
                
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
        super().save(*args, **kwargs)
        update_folder_members(self.project)
        

    def __str__(self) -> str:
        return f'{self.pk}, {self.user}, ({self.project})'


def update_folder_members(project:Project):
    """Update all user permissions for the Grafana folder"""
    user_projects = UserProject.objects.filter(project=project)
    members:dict[str, grafana.FolderPermission] = dict()
    for user_project in user_projects:
        members[user_project.user.username] = grafana.FolderPermission.EDIT if user_project.is_editor else grafana.FolderPermission.VIEW

    grafana.update_folder_permissions(project.name, members)

@receiver(post_delete, sender=User)
def user_post_delete(sender, instance:User, **kwargs):
    """Remove the user from Grafana after they are deleted from the system."""
    grafana.delete_user(instance.username)

@receiver(post_delete, sender=UserProject)
def user_project_post_delete(sender, instance:UserProject, **kwargs):
    """Remove the user from the associated Grafana folder after they are removed from the project."""
    update_folder_members(instance.project)

@receiver(pre_delete, sender=Project)
def project_pre_delete(sender, instance:Project, **kwargs):
    """
    Before a project is deleted, remove the associated InfluxDB bucket and Grafana folder  
    if `PROJECT_AUTO_PURGE` is `True`.
    """
    if PROJECT_AUTO_PURGE:
        influxdb.delete_bucket(instance.name)
        grafana.delete_folder(instance.name)

def clean_name(name:str) -> str:
    '''Remove `"` from name'''
    return name.replace('"', '')
