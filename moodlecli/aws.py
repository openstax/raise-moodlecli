import boto3
import json


def put_json_data(data, bucket_name, key):
    s3_client = boto3.client("s3")
    binary_data = json.dumps(data).encode('utf-8')
    s3_client.put_object(Body=binary_data, Bucket=bucket_name, Key=key)


def get_json_data(bucket_name, key, default=None):
    """This function will attempt to read / parse S3 for JSON data. If it does
    not exist and a default value is provided, it will be returned.
    """
    s3_client = boto3.client("s3")
    try:
        data = s3_client.get_object(Bucket=bucket_name, Key=key)
        contents = data["Body"].read()
        return json.loads(contents)
    except s3_client.exceptions.NoSuchKey as e:
        if default is not None:
            return default
        raise e
