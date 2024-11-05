from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Project, SensorNode, Sensor, UserProject

class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BootstrapModelForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
            

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Uživatelské jméno",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Heslo",
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
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['project'].queryset = Project.objects.filter(userproject__user=user)
    
class ProjectForm(BootstrapModelForm):
    class Meta:
        model = Project
        exclude = ('current_measurement','running')

        

