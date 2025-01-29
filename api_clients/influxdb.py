from influxdb_client import InfluxDBClient, Point, Bucket, PostBucketRequest, Authorization, User, Organization
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from influxdb_client.client.write_api import WriteType, WriteOptions, PointSettings
from influxdb_client import OrganizationsApi, AddResourceMemberRequestBody
from typing import Iterable, TypeAlias, Literal, Generator
from datetime import datetime, tzinfo, timezone, timedelta
import time
from pathlib import Path

ORG = "main"
URL = "http://127.0.0.1:8086"
TOKEN = 'jyoMO_g-zvjqhxZ-ePQ1yfsmxdEQ-E3DJljyXamt_i5CWKfvhqWE18Gd3mWCSfsFbVhbKh-0OiABAMydHuwu7w=='

client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)

WritePrecision: TypeAlias = Literal['s','ms','us','ns']

class Api:
    users = client.users_api()
    auth = client.authorizations_api()
    org = client.organizations_api()
    write = client.write_api()
    bucket = client.buckets_api()
    query = client.query_api()

def get_auth_by_name(name:str) -> Authorization|None:
    for auth in Api.auth.find_authorizations():
        if auth.description == name:
            return auth
        
def get_user_by_name(name:str) -> User|None:
    users = Api.users.find_users(name=name, limit=1).users
    return users[0] if users else None

def get_org_by_name(name:str) -> Organization|None:
    orgs = client.organizations_api().find_organizations(org=name)
    return orgs[0] if orgs else None

def add_organization_member(org_id: str, user_id: str):
    request_body = AddResourceMemberRequestBody(id=user_id)
    return Api.org._organizations_service.post_orgs_id_members(org_id=org_id, add_resource_member_request_body=request_body)

def create_bucket(bucket_name:str) -> Bucket:
    return Api.bucket.create_bucket(org=ORG, bucket_name=bucket_name)

def rename_bucket(current_name:str, new_name:str) -> Bucket|None:
    bucket:Bucket|None = Api.bucket.find_bucket_by_name(current_name)
    if bucket:
        bucket.name = new_name
        return Api.bucket.update_bucket(bucket)
    
def delete_bucket(bucket_name:str) -> Bucket|None:
    bucket:Bucket|None = Api.bucket.find_bucket_by_name(bucket_name)
    if bucket:
        return Api.bucket.delete_bucket(bucket)

def write(bucket_name:str, points:Iterable[Point]):
    return Api.write.write(bucket=bucket_name, org=ORG, record=points)

def create_point(measurement_id, sensor_node_name: str, sensor_name: str, timestamp: int, value: float, write_precision:WritePrecision) -> Point:
    return (
        Point(measurement_id)
        .tag("Sensor Node", sensor_node_name)
        .time(time=timestamp, write_precision=write_precision)
        .field(sensor_name, value)
    )

def query_select(bucket_name:str, measurement_id, limit_n:int, page:int):
    query = f'''
    from(bucket: "{bucket_name}")
    |> range(start: 0)
    |> filter(fn: (r) => r["_measurement"] == "{measurement_id}")
    |> limit(n:{limit_n}, offset: {page*limit_n})  
    '''
    result = Api.query.query(query, ORG)
    return result[0].records if result else []
    
def query_count(bucket_name:str, measurement_id) -> int:
    query = f'''
    from(bucket: "{bucket_name}")
    |> range(start: 0)
    |> filter(fn: (r) => r["_measurement"] == "{measurement_id}")
    |> count()
    '''
    result = Api.query.query(query, ORG)
    return result[0].records[0].get_value() if result else 0

def query_select_all(bucket_name:str, measurement_id, batch_size:int=100_000):
    page = 0
    while True:
        query = f'''
        from(bucket: "{bucket_name}")
        |> range(start: 0)
        |> filter(fn: (r) => r["_measurement"] == "{measurement_id}")
        |> limit(n:{batch_size}, offset: {page*batch_size})  
        '''
        result = Api.query.query(query, ORG)
        if result:
            yield from result[0].records
            page += 1
        else:
            return

def export_csv(bucket_name:str, measurement_id, out_path:Path|str, _timezone:tzinfo, batch_size:int = 100_000):
    open(out_path, 'w').close() # create or clear file
    with open(out_path, 'a') as file:
        file.write('timestamp,value\n')
        for record in query_select_all(bucket_name, measurement_id, batch_size):
            file.write(f'{record.get_time().astimezone(_timezone).isoformat(' ', 'milliseconds')[:-6]},{record.get_value()}\n')
            #print(record.get_time())

if __name__ == '__main__':
    pass