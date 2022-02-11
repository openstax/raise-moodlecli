import boto3
import json


def put_json_data(data, bucket_name, key):
    s3_client = boto3.client("s3")
    binary_data = json.dumps(data).encode('utf-8')
    s3_client.put_object(Body=binary_data, Bucket=bucket_name, Key=key)
