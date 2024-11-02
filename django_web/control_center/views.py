from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect
from django.http import HttpResponse
from django.conf import settings
from django.forms.models import model_to_dict
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required

from .models import User, Project, Measurement, SensorNode, Sensor, UserProject
from .forms import SensorNodeForm
import sqlite3

def index(request):
    return render(request, 'base.html')

def project_list(request):
    context = {}
    context['projects'] = Project.objects.all()
    return render(request, 'project_list.html', context)

# modelformset_factory test
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

    return render(request, 'sensor_formset.html', {'formset': formset})

#@login_required
def sensor_node_edit(request, pk=None):
    context = {}
    sensor_node = get_object_or_404(SensorNode, pk=pk) if pk else None
    
    if request.method == 'POST':
        form = SensorNodeForm(request.POST, instance=sensor_node)
        if form.is_valid():
            form.save()
            return redirect('index')  # Změňte na URL, kam chcete uživatele přesměrovat po uložení
    else:
        user = request.user if request.user.is_authenticated else None
        context['form'] = SensorNodeForm(instance=sensor_node, user=user)
        context['model'] = context['form'].instance.__class__.__name__
        return render(request, 'generic_form.html', context)

