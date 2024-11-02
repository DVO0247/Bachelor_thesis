from django import forms
from .models import User, Project, Measurement, SensorNode, Sensor, UserProject

class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BootstrapModelForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class SensorNodeForm(forms.ModelForm):
    class Meta:
        model = SensorNode
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['project'].queryset = Project.objects.filter(userproject__user=user)

        

