from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Project, SensorNode, Sensor, UserProject, Measurement
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.contrib.auth import forms as auth_forms

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('id',) + UserAdmin.list_display # type: ignore
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': tuple() # additional fields
        }),
    ) # type: ignore
    list_display=UserAdmin.list_display + tuple() # type: ignore # tuple() = additional fields
    

admin.site.register(User, CustomUserAdmin)
admin.site.register(Project)
admin.site.register(Measurement)
admin.site.register(SensorNode)
admin.site.register(Sensor)
admin.site.register(UserProject)
