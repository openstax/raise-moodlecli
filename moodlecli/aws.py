import boto3
from botocore.exceptions import ClientError
import json


def create_bucket_if_doesnt_exist(bucket_name):
    """Create an S3 bucket in a specified region

    :param bucket_name: Bucket to create
    :param region: String region to create bucket in, e.g., 'us-west-2'
    :return: True if bucket created, else False
    """
    try:
        s3_client = boto3.client('s3')
        return s3_client.create_bucket(Bucket=bucket_name)
    except ClientError as e:
        print(e)
        return False
    return True


def send_moodle_sudent_grades_to_bucket(data, bucket_name, key):
    s3_client = boto3.client("s3")
    binary_data = json.dumps(data).encode('utf-8')
    s3_client.put_object(Body=binary_data, Bucket=bucket_name, Key=key)


def print_bucket_key_content(bucket_name, key):
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket_name, key)
    print(obj.get()['Body'].read().decode('utf-8'))


def print_buckets():
    s3 = boto3.resource('s3')
    for bucket in s3.buckets.all():
        print(bucket.name)


def print_bucket_contents(bucket_name):
    s3 = boto3.resource('s3')
    for bucket_object in s3.Bucket(bucket_name).objects.all():
        print(bucket_object.key)
