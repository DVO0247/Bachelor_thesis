# type: ignore
from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.index, name='index'),


    #region Project
    path('project_list/', views.project_list, name='project_list'),
    path('project/<int:project_pk>/details', views.project_details, name='project_details'),
    path('project/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('project/edit/', views.project_edit, name='project_edit'),
    path('project/<int:project_pk>/activate/', views.project_activate, name='project_activate'),
    path('project/<int:project_pk>/deactivate/', views.project_deactivate, name='project_deactivate'),
    path('project/<int:project_pk>/sensor_node_list/', views.project_sensor_node_list, name='project_sensor_node_list'),
    path('project/<int:project_pk>/add/sensor_node/<int:sensor_node_pk>/', views.sensor_node_add_to_project, name='sensor_node_add_to_project'),
    path('project/<int:project_pk>/remove/sensor_node/<int:sensor_node_pk>/', views.sensor_node_remove_from_project, name='sensor_node_remove_from_project'),
    path('project/<int:project_pk>/users/show/', views.project_users_show, name='project_users_show'),
    path('project/<int:project_pk>/users/edit/', views.project_users_edit, name='project_users_edit'),
    path('project/<int:project_pk>/leave/', views.project_leave, name='project_leave'),
    path('reload_active_projects_panel/', views.reload_active_projects_panel, name='reload_active_projects_panel'),


    #region Measurement
    path('project/<int:project_pk>/measurements/', views.measurement_list, name='measurement_list'),
    path('project/<int:project_pk>/measurements/<int:measurement_id>/', views.measurement_data, name='measurement_data'),
    path('project/<int:project_pk>/measurements/<int:measurement_id>/<int:sensor_pk>/explore/1/', views.explore_data, name='explore_data'),
    path('project/<int:project_pk>/measurements/<int:measurement_id>/<int:sensor_pk>/explore/<int:page>/', views.explore_data, name='explore_data'),
    path('project/<int:project_pk>/measurements/<int:measurement_id>/<int:sensor_pk>/explore/goto/', views.explore_data_goto, name='explore_data_goto'),
    path('project/<int:project_pk>/measurements/<int:measurement_id>/<int:sensor_pk>/export/csv/', views.export_csv, name='export_csv'),
    path('project/<int:project_pk>/start/', views.start_measurement, name='start_measurement'),
    path('project/<int:project_pk>/test/', views.start_test_measurement, name='test_measurement'),
    path('project/<int:project_pk>/stop/', views.stop_measurement, name='stop_measurement'),
    path('reload_start_stop_panel/<int:project_pk>/', views.reload_start_stop_panel, name='reload_start_stop_panel'),


    #region SensorNode
    path('sensor_nodes/',views.sensor_node_list, name='sensor_node_list'),
    path('reload_sensor_nodes_table/',views.reload_sensor_nodes_table, name='reload_sensor_nodes_table'),
    path('sensor_node/<int:sensor_node_pk>/edit/', views.sensor_node_edit, name='sensor_node_edit'),
    path('sensor_node/edit/', views.sensor_node_edit, name='sensor_node_edit'),
    path('sensor_node/<int:sensor_node_pk>/edit_sensors/', views.sensor_list, name='sensors_edit'),


    #region Other
    path('delete/<str:model_name>/<int:pk>/', views.delete, name='delete_object'),
    path('toggle_dark_mode/', views.toggle_dark_mode, name='toggle_dark_mode'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('grafana/<path:endpoint>', views.Grafana, name='grafana'),
    path('grafana/', views.Grafana, name='grafana'),
    path('password_change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
]
