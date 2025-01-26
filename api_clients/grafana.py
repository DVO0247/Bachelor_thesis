import requests
from requests.auth import HTTPBasicAuth
from typing import Literal, TypeAlias

URL = 'http://127.0.0.1:3000/'
USERNAME = 'admin'
PASSWORD = 'wsad'
AUTH = HTTPBasicAuth(USERNAME, PASSWORD)
ORG_NAME = 'Main Org.'

Role:TypeAlias = Literal['Viewer', 'Editor', 'Admin']
TeamMembers:TypeAlias = dict[Literal['members', 'admins'], list[str]]

def is_response_ok(response:requests.Response, raise_exception:bool = False) -> bool:
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        if raise_exception:
            raise Exception(f"Error: {response.status_code} - {response.json()['message']}") from e
        else:
            return False
    else:
        return True

def get_org_id(name:str):
    url = f'{URL}/api/orgs/name/{name}'
    response = requests.get(url, auth=AUTH)
    if is_response_ok(response, True):
        return response.json()['id']

ORG_ID = get_org_id(ORG_NAME)

def create_user(name:str, password:str, role:Role = 'Viewer') -> int: # type: ignore
    url = f"{URL}/api/admin/users"

    user = {
        "name": name,
        "email": name,
        "login": name,
        "password": password,
        'orgId': ORG_ID,
        'role': role,
    }

    response = requests.post(url, auth=AUTH, json=user)
    if is_response_ok(response, True):
        return response.json()['id']

def get_user(name:str) -> dict|None:
    url = f"{URL}/api/users?query={name}"

    response = requests.get(url, auth=AUTH)

    if is_response_ok(response, True):
        return response.json()[0] if response.json() else None
    
def delete_user(name:str) -> bool:
    user = get_user(name)
    if user:
        url = f'{URL}/api/admin/users/{user['id']}'
        response = requests.delete(url, auth=AUTH)
        return is_response_ok(response, True)
    return False

def get_org_users():
    url = f'{URL}/api/orgs/{ORG_ID}/users'
    response = requests.get(url, auth=AUTH)
    if is_response_ok(response):
        return response.json()
    
def create_team(name:str) -> int|None:
    url = f'{URL}/api/teams'
    team = {
        "name": name,
        "orgId": ORG_ID
    }
    response = requests.post(url, auth=AUTH, json=team)
    if is_response_ok(response, True):
        return response.json()['teamId']
    else:
        return None
    
def get_team(name:str):
    url = f'{URL}/api/teams/search?name={name}&perpage=1'

    response = requests.get(url, auth=AUTH)
    if is_response_ok(response, True):
        return response.json()['teams'][0] if response.json()['totalCount'] > 0 else None
    
def update_team_members(team_name:str, members:TeamMembers) -> bool:
    team = get_team(team_name)
    if team:
        url = f'{URL}/api/teams/{team['id']}/members'
        response = requests.put(url, auth=AUTH, json=members)
        if is_response_ok(response, True):
            return True
        else:
            return False
    else:
        return False
    
