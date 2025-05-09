"""
This module defines functions for interacting with InfluxDBv2 API.  
These functions are intended to be called from the Control Center, Receiver server and Gradana API client.
"""

from influxdb_client import InfluxDBClient, Point, Bucket, Authorization, User, Organization, Buckets, WriteOptions, Dialect
from influxdb_client import AddResourceMemberRequestBody
from typing import Iterable, TypeAlias, Literal
from datetime import datetime, tzinfo, timezone, timedelta
from pathlib import Path
import tomllib
import os
import logging
from datetime import datetime
log = logging.getLogger(__name__)

APP_DATA_PATH = Path(str(os.getenv('APP_DATA_PATH'))) if os.getenv('APP_DATA_PATH') else Path(__file__).parent.parent/'app_data'

URL = os.getenv('INFLUXDB_URL','http://influxdb:8086')
TOKEN = os.getenv('INFLUXDB_ADMIN_TOKEN', 'jYRq3Qgtk6YarmeE6CZmpdPM3Rk4PF1FjlvMbs-SyXc6ubCkEODlCrkiTVKopYDkrohbe9PRT8Qtgx1iNXcP5w==')
ORG_NAME = os.getenv('INFLUXDB_ORG','main')

client = InfluxDBClient(url=URL, token=TOKEN, org=ORG_NAME)
if not client.ping():
    log.error('Failed to establish connection with Influxdb')

TimePrecision: TypeAlias = Literal['s', 'ms', 'us', 'ns']
DateTimePrecisions: TypeAlias = Literal['hours', 'minutes', 'seconds', 'milliseconds', 'microseconds']


class Api:
    users = client.users_api()
    auth = client.authorizations_api()
    org = client.organizations_api()
    write = client.write_api(WriteOptions(flush_interval=100))
    bucket = client.buckets_api()
    query = client.query_api()
    delete = client.delete_api()

def get_auth_by_name(name: str) -> Authorization | None:
    """Find authorizations by name."""
    for auth in Api.auth.find_authorizations():
        if auth.description == name:
            return auth


def get_user_by_name(name: str) -> User | None:
    users = Api.users.find_users(name=name, limit=1).users
    return users[0] if users else None


def get_org_by_name(name: str) -> Organization | None:
    orgs = client.organizations_api().find_organizations(org=name)
    return orgs[0] if orgs else None


def add_organization_member(org_id: str, user_id: str):
    request_body = AddResourceMemberRequestBody(id=user_id)
    return Api.org._organizations_service.post_orgs_id_members(org_id=org_id, add_resource_member_request_body=request_body)


def create_bucket(bucket_name: str) -> Bucket:
    return Api.bucket.create_bucket(org=ORG_NAME, bucket_name=bucket_name)

def get_buckets() -> list[Bucket]:
    return Api.bucket.find_buckets().buckets

def rename_bucket(current_name: str, new_name: str) -> Bucket | None:
    bucket: Bucket | None = Api.bucket.find_bucket_by_name(current_name)
    if bucket:
        bucket.name = new_name
        return Api.bucket.update_bucket(bucket)


def delete_bucket(bucket_name: str) -> Bucket | None:
    bucket: Bucket | None = Api.bucket.find_bucket_by_name(bucket_name)
    if bucket:
        return Api.bucket.delete_bucket(bucket)


def write(bucket_name: str, points: Iterable[Point]):
    Api.write.write(bucket=bucket_name, org=ORG_NAME, record=points)


def create_point(measurement_id, sensor_node_name: str, sensor_name: str, timestamp: int, value: float, write_precision: TimePrecision) -> Point:
    """Create InfluxDB `Point`"""
    return (
        Point(measurement_id)
        .tag("sensor_node", sensor_node_name)
        .time(time=timestamp, write_precision=write_precision)
        .field(sensor_name, value)
    )


def query_select(bucket_name: str, measurement_id, sensor_node_name: str, sensor_name: str, limit_n: int, page: int):
    query = f'''
    from(bucket: "{bucket_name}")
    |> range(start: 0)
    |> filter(fn: (r) => r["_measurement"] == "{measurement_id}" and r["sensor_node"] == "{sensor_node_name}" and r["_field"] == "{sensor_name}")
    |> limit(n:{limit_n}, offset: {page*limit_n})
    '''
    result = Api.query.query(query, ORG_NAME)
    return result[0].records if result else []

def delete_test_measurement(bucket_name: str):
    Api.delete.delete(datetime.fromtimestamp(0),'2100-01-01T00:00:00Z','_measurement=-1', bucket_name, ORG_NAME)

def query_count(bucket_name: str, measurement_id, sensor_node_name: str, sensor_name: str,) -> int:
    query = f'''
    from(bucket: "{bucket_name}")
    |> range(start: 0)
    |> filter(fn: (r) => r["_measurement"] == "{measurement_id}" and r["sensor_node"] == "{sensor_node_name}" and r["_field"] == "{sensor_name}")
    |> count()
    '''
    result = Api.query.query(query, ORG_NAME)
    return result[0].records[0].get_value() if result else 0


def query_select_all(bucket_name: str, measurement_id, sensor_node_name: str, sensor_name: str, batch_size: int = 100_000):
    """Generator for safely selecting all data for a measurement.  

    This function retrieves data in batches, preventing excessive memory usage  
    by avoiding loading the entire dataset at once.
    """
    page = 0
    while True:
        query = f'''
        from(bucket: "{bucket_name}")
        |> range(start: 0)
        |> filter(fn: (r) => r["_measurement"] == "{measurement_id}" and r["sensor_node"] == "{sensor_node_name}" and r["_field"] == "{sensor_name}")
        |> limit(n:{batch_size}, offset: {page*batch_size})
        '''

        result = Api.query.query(query, ORG_NAME)

        if result:
            yield from result[0].records
            page += 1
        else:
            return

def export_csv(
    bucket_name: str,
    measurement_id,
    sensor_node_name :str,
    sensor_name: str,
    out_path: Path|str,
    ):
    query = f'''
        from(bucket: "{bucket_name}")
        |> range(start: 0)
        |> filter(fn: (r) => r["_measurement"] == "{measurement_id}" and r["sensor_node"] == "{sensor_node_name}" and r["_field"] == "{sensor_name}")
        |> keep(columns: ["_time", "_value"])
    '''

    with open(out_path, 'a') as file:
        file.write('timestamp,value\n')
        rows = Api.query.query_csv(query,ORG_NAME, dialect=Dialect(annotations=[]))

        # return if there are no rows
        try:
            header = next(rows)
        except StopIteration:
            return
        
        time_index = header.index('_time')
        value_index = header.index('_value')
        for row in rows:
            # Time format from 'YYYY-MM-DDTHH:MM:SS.nnnnnnnnnZ' to 'YYYY-MM-DD HH:MM:SS.ssssss'
            file.write(f'{row[time_index][:10]} {row[time_index][11:-1]},{row[value_index]}\n')
