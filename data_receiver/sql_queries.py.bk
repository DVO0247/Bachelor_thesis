SENSOR_NODE_TABLE = 'control_center_sensornode'
PROJECT_TABLE = 'control_center_project'

INITIALIZED_BY_SENSOR_NODE_NAME = f"""
    select name, initialized
    from {SENSOR_NODE_TABLE}
    where name == ?
    limit 1
"""

ALL_PATHS_BY_SENSOR_NODE_NAME = fr"""
    select (p.id||'_'||p.name||'\'||sn.id||'_'||sn.name||'\'||s.id||'_'||s.name||'\'||p.measurement_id||'__'||p.measurement_start_datetime||'.sqlite3') as path
    from {PROJECT_TABLE} p
    join control_center_projectsensornode psn on psn.project_id == p.id
    join control_center_sensornode sn on sn.id == psn.sensor_node_id
    join control_center_sensor s on s.sensor_node_id == sn.id
    where p.running == 1 and sn.name == ?
"""