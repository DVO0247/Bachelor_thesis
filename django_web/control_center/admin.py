from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Project, SensorNode, Sensor, UserProject, Measurement

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('id',) + UserAdmin.list_display # type: ignore
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('darkmode',) # additional fields
        }),
    ) # type: ignore
    list_display=UserAdmin.list_display + tuple() # type: ignore # additional fields belongs to inside tuple
    

admin.site.register(User, CustomUserAdmin)
admin.site.register(Project)
admin.site.register(Measurement)
admin.site.register(SensorNode)
admin.site.register(Sensor)
admin.site.register(UserProject)
