from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Project, SensorNode, Sensor, UserProject
from django.contrib.auth import get_user_model

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
        fields = tuple()
    
class ProjectForm(BootstrapModelForm):
    class Meta:
        model = Project
        fields = ('name','description')

class SensorForm(BootstrapModelForm):
    class Meta:
        model = Sensor
        fields = ('name', 'sample_period', 'samples_per_packet')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            if isinstance(field, forms.IntegerField):
                field.widget.attrs.update({'style': 'width: 120px;'})

class UserProjectForm(forms.Form):
    is_member = forms.BooleanField(required=False, label="Is member")
    is_editor = forms.BooleanField(required=False, label="Is editor")
