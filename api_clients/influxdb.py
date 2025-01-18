from influxdb_client import InfluxDBClient, Point, WritePrecision, Bucket, PostBucketRequest, Authorization, User, Organization
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from influxdb_client.client.write_api import WriteType, WriteOptions, PointSettings
from influxdb_client import OrganizationsApi, AddResourceMemberRequestBody
from typing import Iterable

ORG = "main"
URL = "http://127.0.0.1:8086"
TOKEN = 'jyoMO_g-zvjqhxZ-ePQ1yfsmxdEQ-E3DJljyXamt_i5CWKfvhqWE18Gd3mWCSfsFbVhbKh-0OiABAMydHuwu7w=='

client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)

class Api:
    users = client.users_api()
    auth = client.authorizations_api()
    org = client.organizations_api()
    write = client.write_api()
    bucket = client.buckets_api()

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
