from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Project, Measurement, SensorNode, Sensor, UserProject

class CustomUserAdmin(UserAdmin):
    model = User
    '''
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('test_field',)
        }),
    )
    list_display=UserAdmin.list_display + ('test_field',)
    '''

admin.site.register(User, CustomUserAdmin)
admin.site.register(Project)
admin.site.register(Measurement)
admin.site.register(SensorNode)
admin.site.register(Sensor)
admin.site.register(UserProject)