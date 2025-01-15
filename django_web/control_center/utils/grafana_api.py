from grafana_client import GrafanaApi, TokenAuth
from pathlib import Path

TOKEN = 'glsa_YlGMWAPDAOkMLNFcrQi9kHcPV6a1uLLd_6db139cd'
HOST = '127.0.0.1:3000'
grafana = GrafanaApi(auth=TokenAuth(TOKEN), host=HOST)

def add_source(path:Path|str, name:str):
    _json = {
    'name': name,
    'type': 'frser-sqlite-datasource',
    'access': 'proxy',
    'isDefault': False,
    'editable': True,
    'jsonData': {'path': str(path), 'pathPrefix': 'file:'}
    }
    for k,i in _json.items():
        print(f'{k}: {i}')
    grafana.datasource.create_datasource(_json)

def delete_source(name:str):
    grafana.datasource.delete_datasource_by_name(name)

if __name__ == '__main__':
    pass
