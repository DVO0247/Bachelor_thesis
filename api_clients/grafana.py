"""
This module defines functions for interacting with Grafana's API.  
These functions are intended to be called from the Control Center.
"""

import requests
from requests.auth import HTTPBasicAuth
from typing import Literal, TypeAlias
from enum import Enum
from pathlib import Path
import tomllib
import logging
log = logging.getLogger(__name__)

if __package__:
    from . import influxdb
else:
    import influxdb

CONFIG_FILE_PATH = Path(__file__).parent.parent/'config.toml'

with open(CONFIG_FILE_PATH, 'rb') as file:
    config = tomllib.load(file)['grafana']

GRAFANA_URL = config['url']
ADMIN_USERNAME = config['username']
ADMIN_PASSWORD = config['password']
ORG_NAME = config['org_name']
INFLUXDB_SOURCE_NAME = config['influxdb_source_name']
TOKEN = 'glsa_78Qymplocox2UDAjcfaLX7JtyuySepVi_063aae67'
AUTH = HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD)

Role:TypeAlias = Literal['Viewer', 'Editor', 'Admin']
TeamPermission:TypeAlias = Literal['Member', 'Admin']
TeamMembers:TypeAlias = dict[Literal['members', 'admins'], list[str]]

class FolderPermission(Enum):
    VIEW = 1
    EDIT = 2
    ADMIN = 4

class ResponseException(Exception):
    def __init__(self, response:requests.Response) -> None:
        message = f"Error: {response.status_code} - {response.json()['message']}"
        super().__init__(message)

def is_response_ok(response:requests.Response, raise_exception:bool = False) -> bool:
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        if raise_exception:
            raise ResponseException(response) from e
        else:
            return False
    else:
        return True

def get_org_id(name:str):
    url = f'{GRAFANA_URL}/api/orgs/name/{name}'
    response = requests.get(url, auth=AUTH)
    if is_response_ok(response, True):
        return response.json()['id']

def get_source(source_name:str) -> dict|None:
    url = f'{GRAFANA_URL}/api/datasources/name/{source_name}'
    response = requests.get(url, auth=AUTH)
    if is_response_ok(response, False):
        return response.json()

def add_influxdb_source():
    source = {
        'orgId': ORG_ID,
        'name': f'{INFLUXDB_SOURCE_NAME}',
        'type': 'influxdb',
        'access': 'proxy',
        'url': influxdb.URL,
        'basicAuth': True,
        'basicAuthUser': '',
        'withCredentials': False,
        'isDefault': True, 
        'jsonData': {
            'defaultBucket': 'main',
            'httpMode': 'POST',
            'organization': influxdb.ORG_NAME,
            'version': 'Flux',
        },
        'secureJsonData': {'token': influxdb.TOKEN},
    }

    url = f'{GRAFANA_URL}/api/datasources'
    response = requests.post(url, auth=AUTH, json=source)
    if is_response_ok(response, True):
        return response.json()


try:
    ORG_ID = get_org_id(ORG_NAME)
except requests.exceptions.ConnectionError:
    log.error('Failed to establish connection with Grafana')
else:
    if not get_source(INFLUXDB_SOURCE_NAME):
        if add_influxdb_source():
            log.info('InfluxDB source added to Grafana')


def delete_source(source_name:str):
    url = f'{GRAFANA_URL}/api/datasources/name/{source_name}'
    response = requests.delete(url, auth=AUTH)
    if is_response_ok(response, True):
        return response.json()

def create_user(name:str, password:str, role:Role = 'Viewer') -> int: # type: ignore
    url = f"{GRAFANA_URL}/api/admin/users"

    user = {
        "name": name,
        "email": name,
        "login": name,
        "password": password,
        'orgId': ORG_ID,
        'role': role,
    }

    response = requests.post(url, auth=AUTH, json=user)
    if response.status_code == 412:
        log.error(f"User with email '{user['email']}' or username '{user['name']}' already exists")
        return -1
    elif is_response_ok(response, True):
        return response.json()['id']

def get_user(name:str) -> dict|None:
    url = f"{GRAFANA_URL}/api/users?query={name}"

    response = requests.get(url, auth=AUTH)

    if is_response_ok(response, True):
        return response.json()[0] if response.json() else None
    
def delete_user(name:str) -> bool:
    user = get_user(name)
    if user:
        url = f'{GRAFANA_URL}/api/admin/users/{user['id']}'
        response = requests.delete(url, auth=AUTH)
        return is_response_ok(response, True)
    return False

def get_org_users():
    url = f'{GRAFANA_URL}/api/orgs/{ORG_ID}/users'
    response = requests.get(url, auth=AUTH)
    if is_response_ok(response):
        return response.json()
    
def create_team(name:str) -> int|None:
    url = f'{GRAFANA_URL}/api/teams'
    team = {
        "name": name,
        "orgId": ORG_ID
    }
    response = requests.post(url, auth=AUTH, json=team)
    if is_response_ok(response, True):
        return response.json()['teamId']
    else:
        return None
    
def get_team(team_name:str):
    url = f'{GRAFANA_URL}/api/teams/search?name={team_name}&perpage=1'

    response = requests.get(url, auth=AUTH)
    if is_response_ok(response, True):
        return response.json()['teams'][0] if response.json()['totalCount'] > 0 else None

def get_team_members(team_name:str):
    team = get_team(team_name)
    if team:
        url = f'{GRAFANA_URL}/api/teams/{team['id']}/members'
        response = requests.get(url, auth=AUTH)
        return response.json()
    return False

def delete_team(team_name:str):
    team = get_team(team_name)
    if team:
        url = f'{GRAFANA_URL}/api/teams/{team['id']}'
        response = requests.delete(url, auth=AUTH)
        if is_response_ok(response, True):
            return True
    return False

def update_team_members(team_name:str, members:TeamMembers) -> bool:
    team = get_team(team_name)
    if team:
        url = f'{GRAFANA_URL}/api/teams/{team['id']}/members'
        response = requests.put(url, auth=AUTH, json=members)
        if is_response_ok(response, True):
            return True
    return False

def add_team_member(team_name:str, username:str):
    team = get_team(team_name)
    user = get_user(username)
    if team and user:
        url = f'{GRAFANA_URL}/api/teams/{team['id']}/members'
        data = {"userId": user['id']}
        response = requests.post(url, auth=AUTH, json=data)
        if is_response_ok(response, True):
            return True
    return False

def remove_team_member(team_name:str, username:str):
    team = get_team(team_name)
    user = get_user(username)
    if team and user:
        url = f'{GRAFANA_URL}/api/teams/{team['id']}/members/{user['id']}'
        response = requests.delete(url, auth=AUTH)
        if is_response_ok(response, True):
            return True
    return False
    
def change_user_password(username:str, new_password:str) -> bool:
    if username == ADMIN_USERNAME:
        log.warning(f'{ADMIN_USERNAME} password should be changed manually in Grafana')
        return False
    user = get_user(username)
    if user:
        data = {'password': new_password}
        url = f"{GRAFANA_URL}/api/admin/users/{user['id']}/password"
        response = requests.put(url, auth=AUTH, json=data)
        if is_response_ok(response, False):
            return True
        else:
            log.error(response.json())
    return False

def change_user_email(username:str, new_email:str) -> bool:
    user = get_user(username)
    if user:
        data = {'email': new_email}
        url = f"{GRAFANA_URL}/api/users/{user['id']}"
        response = requests.put(url, auth=AUTH, json=data)
        if is_response_ok(response, True):
            return True
    return False

def change_user_role(username:str, role:Role):
    user = get_user(username)
    if user:
        data = {'role': role}
        url = f'{GRAFANA_URL}/api/orgs/{ORG_ID}/users/{user['id']}'
        response = requests.patch(url, auth=AUTH, json=data)
        if is_response_ok(response, True):
            return True
    return False

def get_folder(folder_name:str):
    url = f'{GRAFANA_URL}/api/folders'
    response = requests.get(url, auth=AUTH)
    if is_response_ok(response, True):
        for folder in response.json():
            if folder['title'] ==  folder_name:
                return folder
    return False

def create_folder(folder_name:str):
    url = f'{GRAFANA_URL}/api/folders'
    folder = {'title': folder_name}
    response = requests.post(url, auth=AUTH, json=folder)
    if is_response_ok(response, True):
        return True
    return False

def delete_folder(folder_name:str):
    folder = get_folder(folder_name)
    if folder:
        url = f'{GRAFANA_URL}/api/folders/{folder['uid']}'
        response = requests.delete(url, auth=AUTH)
        if is_response_ok(response, True):
            return True
    return False

def update_folder_permissions(folder_name:str, members:dict[str, FolderPermission]):
    folder = get_folder(folder_name)
    member_ids:dict[int, FolderPermission] = dict()
    for name, perm in members.items():
        user = get_user(name)
        if user:
            member_ids[user['id']] = perm
    if folder and member_ids:
        url = f'{GRAFANA_URL}/api/folders/{folder['uid']}/permissions'
        permissions:dict[str, list[dict[str, str|int]]] = {
            'items': [
                {
                'role': 'Admin',
                'permission': FolderPermission.ADMIN.value
                }
            ]
        }
        for id, perm in member_ids.items():
            permissions['items'].append({"userId": id, 'permission': perm.value})
        
        response = requests.post(url, auth=AUTH, json=permissions)
        if is_response_ok(response, True):
            return True
    return False

def rename_folder(old_folder_name:str, new_folder_name:str):
    folder = get_folder(old_folder_name)
    if folder:
        url = f'{GRAFANA_URL}/api/folders/{folder['uid']}'
        data = {
            'title': new_folder_name,
            'overwrite': True
        }
        response = requests.put(url, auth=AUTH, json=data)
        if is_response_ok(response, True):
            return True
    return False
