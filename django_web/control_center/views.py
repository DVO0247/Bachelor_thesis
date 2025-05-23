from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect, StreamingHttpResponse
from django.core.exceptions import PermissionDenied
from django.forms import modelformset_factory
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib import messages
from django.apps import apps
from django.utils import timezone
from django.urls import reverse_lazy

from pathlib import Path
import os

from .models import User, Project, SensorNode, Sensor, UserProject, Measurement, SensorNodeTypes
from .forms import SensorNodeForm, ProjectForm, LoginForm, SensorForm, UserProjectForm
from api_clients import influxdb, grafana


TEMP_DIR_PATH = Path(__file__).parent/'temp' 

def index(request):
    return redirect('project_list')

#region User
def user_details(request):
    ...
#endrefion

#region Project
def project_list(request):
    context = {}
    context['projects'] = Project.objects.all()
    return render(request, 'project_list.html', context)

def project_dashboard(request, project_pk):
    context = {}
    project = get_object_or_404(Project, pk=project_pk)
    context['project_sensor_nodes'] = project.sensor_nodes.all()
    context['user_project'] = get_object_or_404(UserProject, user=request.user, project=project)
    context['all_user_projects'] = UserProject.objects.filter(project=project)
    grafana_folder = grafana.get_folder(project.name)
    context['grafana_endpoint'] = f'dashboards/f/{grafana_folder['uid']}' if grafana_folder else None
    return render(request, 'project_dashboard.html', context)


def project_edit(request, pk=None):
    context = {}
    instance = get_object_or_404(Project, pk=pk) if pk else None
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=instance)
        if form.is_valid():
            project = form.save()
            if instance is None:
                user_project = UserProject(user=request.user, project=project, is_owner=True)
                user_project.save()
            previous_url = request.POST.get('previous_url')
            if not previous_url:
                previous_url = 'index'
            return redirect(previous_url)
        
    else:
        context['form'] = ProjectForm(instance=instance)
        context['model'] = context['form'].instance.__class__.__name__
        if pk:
            context['user_project'] = get_object_or_404(UserProject, user=request.user, project=pk)
        return render(request, 'project_edit.html', context)

def project_activate(request, project_pk):
    """Add project to user's activated project list"""
    if request.method == 'POST':
        user_project = get_object_or_404(UserProject, project=project_pk, user=request.user)
        
        user_project.is_activated = True
        user_project.save()
        previous_url = request.POST.get('previous_url')
        if not previous_url:
            previous_url = 'index'
        return redirect(request.META['HTTP_REFERER'])
    
def project_deactivate(request, project_pk):
    """Remove project from user's activated project list"""
    if request.method == 'POST':
        user_project = get_object_or_404(UserProject, project=project_pk, user=request.user)
        
        user_project.is_activated = False
        user_project.save()
        # stop if noone has activated this project
        if UserProject.objects.filter(project=project_pk, is_activated=True).count() == 0:
            stop_measurement(request,project_pk)
            
        previous_url = request.POST.get('previous_url')
        if not previous_url:
            previous_url = 'index'
        return redirect(request.META['HTTP_REFERER'])

def project_sensor_node_list(request, project_pk):
    context = {}
    project = get_object_or_404(Project, pk=project_pk)
    context['sensor_nodes'] = SensorNode.objects.all()
    context['project_sensor_nodes'] = project.sensor_nodes.all()
    context['user_project'] = get_object_or_404(UserProject, user=request.user, project=project)
    #context['project'] = project
    return render(request, 'project_sensor_node_list.html', context)

def sensor_node_add_to_project(request, project_pk, sensor_node_pk):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=project_pk)
        if not project.is_running():
            sensor_node = get_object_or_404(SensorNode, pk=sensor_node_pk)
            project.sensor_nodes.add(sensor_node)
            project.save()
        return redirect('project_sensor_node_list', project_pk=project_pk)
    
def sensor_node_remove_from_project(request, project_pk, sensor_node_pk):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=project_pk)
        sensor_node = get_object_or_404(SensorNode, pk=sensor_node_pk)
        project.sensor_nodes.remove(sensor_node)
        project.save()
        return redirect('project_sensor_node_list', project_pk=project_pk)

def project_users_show(request, project_pk):
    user_projects = UserProject.objects.filter(project=project_pk)
    if any(request.user == user_project.user for user_project in user_projects):
        context = {'this_user_projects':user_projects}
        return render(request, 'project_users_show.html', context)
    else:
        raise PermissionDenied


def project_users_edit(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    users = User.objects.all()
    user_forms = {}

    if request.method == 'POST':
        for user in users:
            form = UserProjectForm(request.POST, prefix=str(user.pk))
            if form.is_valid():
                user_project = UserProject.objects.filter(user=user, project=project).first()
                # Check if the user is not already in project
                if not user_project:
                    user_project = UserProject(user=user, project=project)
                    is_already_member = False
                else:
                    is_already_member = True

                if user_project.is_owner:
                    continue # Don't change permission for owner
                
                is_member = form.cleaned_data.get('is_member', False)
                is_editor = form.cleaned_data.get('is_editor', False)

                user_project.is_editor = is_editor

                if not is_member:
                    if is_already_member:
                        user_project.delete()
                else:
                    user_project.save()
        previous_url = request.POST.get('previous_url')
        if not previous_url:
            previous_url = 'index'
        return redirect(previous_url)

    else:
        user_projects = UserProject.objects.filter(project=project)
        user_project_owner = user_projects.filter(is_owner=True).first()
        for user in users:
            user_project = user_projects.filter(user=user).first()
            initial_data = {
                'is_member': True if user_project else False,
                'is_editor': user_project.is_editor if user_project else False
            }

            form = UserProjectForm(initial=initial_data, prefix=str(user.pk))
            
            if user_project_owner and user == user_project_owner.user:
                # Disable form fields for the owner
                form.fields['is_member'].widget.attrs['disabled'] = 'disabled'
                form.fields['is_editor'].widget.attrs['disabled'] = 'disabled'
            
            user_forms[user] = form
    context = {'project': project,'user_forms': user_forms}
    return render(request, 'project_users_edit.html', context)

def project_leave(request, project_pk):
    user_project = get_object_or_404(UserProject, user=request.user, project=project_pk)
    user_project.delete()
    return redirect('project_list')

def reload_active_projects_panel(request):
    """
    Reload sidebar active projects panel.
    Called by htmlx.
    """
    return render(request, r'includes/active_projects_panel.html')
#endregion

#region Measurement
def measurement_list(request, project_pk):
    """List of all measurement for the project"""
    context = {}
    project = get_object_or_404(Project, pk=project_pk)
    context['project'] = project
    context['measurements'] = Measurement.objects.filter(project=project).order_by('-pk')
    return render(request, 'measurement_list.html', context)

def measurement_data(request, project_pk, measurement_id):
    """Show all sensor nodes and it's sensors asociated with measurement"""
    context = {}
    project = get_object_or_404(Project, pk=project_pk)
    measurement = get_object_or_404(Measurement, project=project, id_in_project=measurement_id)
    context['measurement'] = measurement
    context['project'] = project
    return render(request, 'measurement_data.html', context)

def explore_data(request, project_pk, measurement_id, sensor_pk, page=1, limit_n=50):
    context = {}
    project = get_object_or_404(Project, pk=project_pk)
    measurement = get_object_or_404(Measurement, project=project, id_in_project=measurement_id)
    sensor = get_object_or_404(Sensor, pk=sensor_pk)
    sensor_node = sensor.sensor_node
    record_count = influxdb.query_count(project.name, measurement.id_in_project, sensor_node.name, sensor.name) # type: ignore
    page_count = record_count//limit_n if record_count % limit_n == 0 else record_count//limit_n + 1
    records = influxdb.query_select(project.name, measurement.id_in_project, sensor_node.name, sensor.name, limit_n, page-1) # type: ignore
    current_timezone = timezone.get_current_timezone()
    context['records'] = (
        (
            record.get_time().astimezone(current_timezone).isoformat(' ', 'microseconds')[:-6],
            record.get_value()
        )
        for record in records
        )
    context['page'] = page
    context['page_count'] = page_count
    context['pages'] = range(1, page_count+1)
    context['measurement'] = measurement
    context['sensor'] = sensor
    context['project'] = project
    context['add_page_field_size'] = len(str(page_count))*10
    return render(request, 'explore_data.html', context)

def explore_data_goto(request, project_pk, measurement_id, sensor_pk, count=50):
    """Redirect to explore data view"""
    page = int(request.POST.get('page', 1))
    return redirect('explore_data', project_pk=project_pk, measurement_id=measurement_id, sensor_pk=sensor_pk, page=page)

def export_csv(request, project_pk, measurement_id, sensor_pk):
    TEMP_DIR_PATH.mkdir(exist_ok=True)
    project = get_object_or_404(Project, pk=project_pk)
    measurement= get_object_or_404(Measurement, project=project, id_in_project=measurement_id)
    sensor = get_object_or_404(Sensor, pk=sensor_pk)
    sensor_node = sensor.sensor_node
    filename = f'{project.name}_{sensor.sensor_node.name}_{sensor.name}_{measurement.id_in_project}_{measurement.start_time.isoformat(timespec='milliseconds')[:-6]}.csv'

    i = 0
    while True:
        temp_file_path = TEMP_DIR_PATH/f'export_{i}.csv'
        if not temp_file_path.exists():
            break
        else:
            i+=1
    
    influxdb.export_csv(project.name, measurement.id_in_project, sensor_node.name, sensor.name, temp_file_path) # type: ignore

    def file_iterator(path, chunk_size=8192):
        with open(path, 'rb') as f:
            while chunk := f.read(chunk_size):
                yield chunk

        # Remove file after download
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
    
    response = StreamingHttpResponse(file_iterator(temp_file_path), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response

def start_measurement(request, project_pk):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=project_pk)
        project.start_measurement()
        from_panel = request.POST.get('from_panel', False)
        if from_panel:
            return reload_active_projects_panel(request)
        else:
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
        

def start_test_measurement(request, project_pk):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=project_pk)
        project.start_test_measurement()
        from_panel = request.POST.get('from_panel', False)
        if from_panel:
            return reload_active_projects_panel(request)
        else:
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

 
def stop_measurement(request, project_pk):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=project_pk)
        project.stop_measurement()
        from_panel = request.POST.get('from_panel', False)
        if from_panel:
            return reload_active_projects_panel(request)
        else:
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

def reload_start_stop_panel(request, project_pk):
    """
    Reload start stop panel.
    Called by htmlx.
    """
    project = get_object_or_404(Project, pk=project_pk)
    context = {'project':project}
    return render(request, r'includes/start_stop_panel.html', context)
#endregion

#region SensorNode
def sensor_node_list(request):
    context = {}
    context['sensor_nodes'] = SensorNode.objects.all()
    return render(request, 'sensor_node_list.html', context)

def reload_sensor_nodes_table(request):
    """
    Reload table of all sensor nodes.
    Called by htmlx.
    """
    context = {}
    context['sensor_nodes'] = SensorNode.objects.all()
    return render(request, r'includes/sensor_nodes_table.html', context)

def sensor_node_edit(request, sensor_node_pk=None):
    context = {}
    sensor_node = get_object_or_404(SensorNode, pk=sensor_node_pk) if sensor_node_pk else None
    
    if request.method == 'POST':
        form = SensorNodeForm(request.POST, instance=sensor_node)
        if form.is_valid():
            form.save()
            previous_url = request.POST.get('previous_url')
            if not previous_url:
                previous_url = 'index'
            return redirect(previous_url)
    else:
        context['form'] = SensorNodeForm(instance=sensor_node)
        context['model'] = context['form'].instance.__class__.__name__
        return render(request, 'generic_form.html', context)
#endregion

#region Sensor
SensorFormSet = modelformset_factory(Sensor, form=SensorForm, extra=0)

def sensor_list(request, sensor_node_pk):
    if request.method == 'POST':
        sensor_node = get_object_or_404(SensorNode, pk=sensor_node_pk)
        formset = SensorFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            sensor_node.initialized = True
            sensor_node.save()
            previous_url = request.POST.get('previous_url')
            if not previous_url:
                previous_url = 'index'
            return redirect(previous_url)
        else:
            context = {
                    'formset': formset,
                    'sensor_node': sensor_node
                }
            return render(request, 'sensor_formset.html', context)
    else:
        context = {}
        context['formset'] = SensorFormSet(queryset=Sensor.objects.filter(sensor_node=sensor_node_pk))
        context['sensor_node'] = get_object_or_404(SensorNode, pk=sensor_node_pk)
        return render(request, 'sensor_formset.html', context)
#endrefion

#region Other
def delete(request, model_name, pk):
    """Generic object delete function"""
    if request.method == 'POST':
        Model = apps.get_model('control_center', model_name)

        obj = get_object_or_404(Model, pk=pk)
        obj.delete()
        if isinstance(obj, Project):
            return redirect(index)
        else:
            previous_url = request.POST.get('previous_url')
            if not previous_url:
                previous_url = 'index'
            return redirect(previous_url)

def toggle_dark_mode(request):
    user = request.user
    user.darkmode = not user.darkmode
    user.save()
    return JsonResponse({'darkmode': user.darkmode})

class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'login.html'

    def form_invalid(self, form):
        messages.error(self.request, "Wrong password or username.")
        return super().form_invalid(form)

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'password_change.html'
    success_url = reverse_lazy('index')

def Grafana(request, endpoint:str = 'dashboards'):
    """Redirect to Grafana by client IP"""
    ip = request.get_host().split(':')[0]
    return HttpResponseRedirect(f'http://{ip}:3000/{endpoint}')
#endrefion
