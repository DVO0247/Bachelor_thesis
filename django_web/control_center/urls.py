from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('projects/', views.project_list, name='project_list'),
    path('sensors/', views.sensor_view, name='sensor_view'),
    path('create/<int:pk>', views.sensor_node_edit, name='sensor_node_edit'),
    path('create/', views.sensor_node_edit, name='sensor_node_edit'),

]