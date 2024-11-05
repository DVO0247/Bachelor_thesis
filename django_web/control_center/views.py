from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.forms.models import model_to_dict
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.apps import apps

from .models import User, Project, SensorNode, Sensor, UserProject, ProjectSensorNode
from .forms import SensorNodeForm, ProjectForm, LoginForm
import sqlite3

def index(request):
    return redirect('project_list')

#region Project
def project_list(request):
    context = {}
    context['projects'] = Project.objects.all()
    return render(request, 'project_list.html', context)

def project(request, pk):
    context = {}
    project = get_object_or_404(Project, pk=pk)
    context['sensor_nodes'] = SensorNode.objects.filter(project=project)
    context['project'] = project
    return ...
    return render(request, 'project.html', context)

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
        return render(request, 'generic_form.html', context)

def project_use(request, pk=None):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=pk) if pk else None
        user:User = request.user
        user.current_project = project
        user.save()
        '''if project:
            project.running = False
            project.save()'''
        previous_url = request.POST.get('previous_url')
        if not previous_url:
            previous_url = 'index'
        return redirect(previous_url)
#endregion

#region Measurement
def start_measurement(request):
    if request.method == 'POST':
        project:Project = request.user.current_project
        project.new_measurement()
        project.save()
        '''previous_url = request.POST.get('previous_url')
        if not previous_url:
            previous_url = 'index'
            '''
        return render(request,'includes\\start_stop.html')
    
def stop_measurement(request):
    if request.method == 'POST':
        project = request.user.current_project
        project.running = False
        project.measurement_id+=1
        project.save()
        return render(request,'includes\\start_stop.html')
    
def reload_measurement(request):
    return render(request, 'includes\\start_stop.html')
#endregion

#region SensorNode
def sensor_node_list(request, project_pk):
    context = {}
    project = get_object_or_404(Project, pk=project_pk)
    context['sensor_nodes'] = SensorNode.objects.all()
    context['project_sensor_nodes'] = SensorNode.objects.filter(projectsensornode__project=project)
    context['project'] = project
    return render(request, 'sensor_node_list.html', context)

def sensor_node_add_to_project(request, project_pk, sensor_node_pk):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=project_pk)
        sensor_node = get_object_or_404(SensorNode, pk=sensor_node_pk)
        project_sensor_node = ProjectSensorNode(project=project, sensor_node=sensor_node)
        project_sensor_node.save()
        return redirect('sensor_node_list', project_pk=project_pk)
    
def sensor_node_remove_from_project(request, project_pk, sensor_node_pk):
    if request.method == 'POST':
        project_sensor_node = get_object_or_404(ProjectSensorNode,project=project_pk, sensor_node=sensor_node_pk)
        project_sensor_node.delete()
        return redirect('sensor_node_list', project_pk=project_pk)

def sensor_node_edit(request, pk=None):
    context = {}
    sensor_node = get_object_or_404(SensorNode, pk=pk) if pk else None
    
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
def sensor_list(request, sensor_node_pk):
    context = {}
    
    return render(request, ..., context)
#endrefion

#region Other
def delete(request, model_name, pk):
    if request.method == 'POST':
        Model = apps.get_model('control_center',model_name)

        obj = get_object_or_404(Model, pk=pk)
        obj.delete()
        previous_url = request.POST.get('previous_url')
        if not previous_url:
            previous_url = 'index'
        return redirect(previous_url)

def toggle_dark_mode(request):
    user = request.user
    user.darkmode = not user.darkmode  # Přepínání hodnoty
    user.save()
    return JsonResponse({'darkmode': user.darkmode})

class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'login.html'

    def form_invalid(self, form):
        # Přidat chybovou zprávu, pokud je přihlášení neplatné
        messages.error(self.request, "Wrong password or username.")
        return super().form_invalid(form)
    
'''# modelformset_factory test
SensorFormSet = modelformset_factory(
    Sensor,
    fields='__all__',  # Přizpůsobte pole podle potřeby
    extra=0  # Počet prázdných formulářů pro přidání nových senzorů
)
def sensor_view(request):
    if request.method == 'POST':
        formset = SensorFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('index')  # Upravte na URL pro přesměrování po úspěšném uložení
    else:
        formset = SensorFormSet(queryset=Sensor.objects.all())

    return render(request, 'sensor_formset.html', {'formset': formset})'''
#endregion