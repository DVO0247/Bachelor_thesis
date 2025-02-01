from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, FileResponse
from django.core.exceptions import PermissionDenied
from django.core.files.temp import NamedTemporaryFile
from django.conf import settings
from django.forms.models import model_to_dict
from django.forms import modelformset_factory
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.apps import apps
from django.utils import timezone

from pathlib import Path

from .models import User, Project, SensorNode, Sensor, UserProject, Measurement, SensorNodeTypes
from .forms import SensorNodeForm, ProjectForm, LoginForm, SensorForm, UserProjectForm
from api_clients import influxdb
from api_clients import grafana

TEMP_DIR_PATH = Path.cwd()/'control_center'/'temp' 

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

def project_details(request, project_pk):
    context = {}
    project = get_object_or_404(Project, pk=project_pk)
    context['sensor_nodes'] = SensorNode.objects.all()
    context['project_sensor_nodes'] = project.sensor_nodes.all()
    context['user_project'] = get_object_or_404(UserProject, user=request.user, project=project)
    context['this_user_projects'] = UserProject.objects.filter(project=project)
    #context['project'] = project
    return render(request, 'project_details.html', context)


def project_edit(request, pk=None):
    context = {}
    instance = get_object_or_404(Project, pk=pk) if pk else None
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=instance)
        if form.is_valid():
            project = form.save()
            if instance is None:
                userproject = UserProject(user=request.user, project=project, is_owner=True)
                userproject.save()
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
    if request.method == 'POST':
        user_project = get_object_or_404(UserProject, project=project_pk, user=request.user)
        
        user_project.is_activated = True
        user_project.save()
        previous_url = request.POST.get('previous_url')
        if not previous_url:
            previous_url = 'index'
        return redirect(request.META['HTTP_REFERER'])
    
def project_deactivate(request, project_pk):
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
                if not user_project:
                    user_project = UserProject(user=user, project=project)
                    new = True
                else:
                    new = False
                #user_project, created = UserProject.objects.get_or_create(user=user, project=project)
                if user_project.is_owner:
                    continue
                
                is_member = form.cleaned_data.get('is_member', False)
                is_editor = form.cleaned_data.get('is_editor', False)

                user_project.is_editor = is_editor

                if not is_member:
                    if not new:
                        user_project.delete()
                else:
                    user_project.save()
        previous_url = request.POST.get('previous_url')
        if not previous_url:
            previous_url = 'index'
        return redirect(previous_url)

    else:
        user_projects = UserProject.objects.filter(project=project)
        owner = user_projects.filter(is_owner=True).first()
        for user in users:
            user_project = user_projects.filter(user=user).first()
            initial_data = {
                'is_member': True if user_project else False,
                'is_editor': user_project.is_editor if user_project else False
            }

            form = UserProjectForm(initial=initial_data, prefix=str(user.pk))
            
            # Pokud je uživatel aktuálně přihlášený, nastavíme atribut `disabled`
            if owner and user == owner.user:
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
    return render(request, r'includes/active_projects_panel.html')
#endregion

#region Measurement
def measurement_list(request, project_pk):
    context = {}
    project = get_object_or_404(Project, pk=project_pk)
    context['project'] = project
    context['measurements'] = Measurement.objects.filter(project=project).order_by('-pk')
    return render(request, 'measurement_list.html', context)

def measurement_data(request, project_pk, measurement_id):
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
    record_count = influxdb.query_count(project.name, measurement.id_in_project)
    page_count = record_count//limit_n if record_count % limit_n == 0 else record_count//limit_n + 1
    records = influxdb.query_select(project.name, measurement.id_in_project, limit_n, page-1)
    current_timezone = timezone.get_current_timezone()
    context['records'] = (
        (
            record.get_time().astimezone(current_timezone).isoformat(' ', 'milliseconds')[:-6],
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
    page = int(request.POST.get('page', 1))
    return redirect('explore_data', project_pk=project_pk, measurement_id=measurement_id, sensor_pk=sensor_pk, page=page)

def export_csv(request, project_pk, measurement_id, sensor_pk):
    TEMP_DIR_PATH.mkdir(exist_ok=True)
    out_path = TEMP_DIR_PATH/'export.csv'
    project = get_object_or_404(Project, pk=project_pk)
    measurement= get_object_or_404(Measurement, project=project, id_in_project=measurement_id)
    sensor = get_object_or_404(Sensor, pk=sensor_pk)
    influxdb.export_csv(project.name, measurement.id_in_project, out_path, timezone.get_current_timezone(), 100_000)
    filename = f'{project.name}_{sensor.sensor_node.name}_{sensor.name}_{measurement.id_in_project}_{measurement.start_time.isoformat(timespec='milliseconds')[:-6]}.csv'

    return FileResponse(open(out_path, 'rb'), as_attachment=True, filename=filename)

def start_measurement(request, project_pk):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=project_pk)
        project.start_measurement()
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
    if request.method == 'POST':
        Model = apps.get_model('control_center',model_name)

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
    
def Grafana(request):
    return HttpResponseRedirect('http://127.0.0.1:3000/dashboards') # TODO: redirect to outside IP
#endrefion
