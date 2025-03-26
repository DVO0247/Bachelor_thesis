from django.core.management.base import BaseCommand, CommandParser
from control_center.models import Project
from api_clients import influxdb

class Command(BaseCommand):
    help = 'Resync Control center projects with InfluxDB buckets'
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--clear', action='store_true', help="Remove all buckets that do not have a corresponding project in the Control Center.")
    
    def handle(self, *args, **options):
        influxdb_project_names: set[str] = set(bucket.name for bucket in influxdb.get_buckets()) # type: ignore
        projects_names = set(Project.objects.values_list('name', flat=True))
        
        projects_not_in_influxdb = projects_names - influxdb_project_names
        for project_name in projects_not_in_influxdb:
            influxdb.create_bucket(project_name)
            print(f'InfluxDB bucket "{project_name}" added')

        if options['clear']:
            projects_not_in_control_center = influxdb_project_names - projects_names
            for project_name in projects_not_in_control_center:
                influxdb.delete_bucket(project_name)
                print(f'InfluxDB bucket "{project_name}" removed')
