from django.core.management.base import BaseCommand, CommandParser
from control_center.models import Project, update_folder_members
from api_clients import grafana
import os

class Command(BaseCommand):
    help = 'Resync Control center projects with Grafana folders'
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--clear', action='store_true', help="Remove all folders that do not have a corresponding project in the Control Center.")
    
    def handle(self, *args, **options):
        grafana_project_names = set(folder['title'] for folder in grafana.get_folders())
        projects_names = set(Project.objects.values_list('name', flat=True))
        
        projects_not_in_grafana = projects_names - grafana_project_names
        for project_name in projects_not_in_grafana :
            grafana.create_folder(project_name)
            update_folder_members(Project.objects.get(name=project_name))
            grafana.create_dashboard(project_name)
            print(f'Grafana folder "{project_name}" added')

        if options['clear']:
            projects_not_in_control_center = grafana_project_names - projects_names
            for project_name in projects_not_in_control_center:
                grafana.delete_folder(project_name)
                print(f'Grafana folder "{project_name}" removed')
