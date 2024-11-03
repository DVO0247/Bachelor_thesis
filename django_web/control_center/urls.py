from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('projects/', views.project_list, name='project_list'),
    path('project/<int:pk>', views.project, name='project'),
    path('project_edit/<int:pk>', views.project_edit, name='project_edit'),
    path('project_edit/', views.project_edit, name='project_edit'),
    path('project_use/<int:pk>', views.project_use, name='project_use'),
    path('sensors/', views.sensor_view, name='sensor_view'),
    path('create/<int:pk>', views.sensor_node_edit, name='sensor_node_edit'),
    path('create/', views.sensor_node_edit, name='sensor_node_edit'),
    path('delete/<str:model_name>/<int:pk>/', views.delete, name='delete_object'),
]