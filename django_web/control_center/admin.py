from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Project, SensorNode, Sensor, UserProject

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('id',) + UserAdmin.list_display # type: ignore
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('current_project',)
        }),
    ) # type: ignore
    list_display=UserAdmin.list_display + ('current_project',) # type: ignore

admin.site.register(User, CustomUserAdmin)
admin.site.register(Project)
admin.site.register(SensorNode)
admin.site.register(Sensor)
admin.site.register(UserProject)
