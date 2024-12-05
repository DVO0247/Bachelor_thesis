from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Project, SensorNode, Sensor

class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BootstrapModelForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': 4})
            if isinstance(field, forms.BooleanField):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
            
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class SensorNodeForm(BootstrapModelForm):
    class Meta:
        model = SensorNode
        fields = '__all__'
    
class ProjectForm(BootstrapModelForm):
    class Meta:
        model = Project
        exclude = ('current_measurement','running')

class SensorForm(BootstrapModelForm):
    class Meta:
        model = Sensor
        fields = ('name','sample_period','samples_per_packet')