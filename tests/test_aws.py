from moodlecli import aws
import boto3
import botocore.stub
import io
import json
import pytest


def test_get_json_data_existing(mocker):
    s3_client = boto3.client("s3")
    stubber = botocore.stub.Stubber(s3_client)

    test_key = "data.json"
    test_bucket = "test-bucket"
    test_data = {
        "foo": "bar"
    }

    stubber.add_response(
        "get_object",
        {"Body": io.BytesIO(json.dumps(test_data).encode('utf-8'))},
        expected_params={
            "Bucket": test_bucket,
            "Key": test_key,
        }
    )
    stubber.activate()
    mocker.patch("boto3.client", lambda service: s3_client)

    res = aws.get_json_data(test_bucket, test_key)
    stubber.assert_no_pending_responses()
    assert res == test_data


def test_get_json_data_raise_nonexisting(mocker):
    s3_client = boto3.client("s3")
    stubber = botocore.stub.Stubber(s3_client)

    test_key = "data.json"
    test_bucket = "test-bucket"

    stubber.add_client_error(
        "get_object",
        service_error_code="NoSuchKey",
        expected_params={
            "Bucket": test_bucket,
            "Key": test_key,
        },
    )
    stubber.activate()
    mocker.patch("boto3.client", lambda service: s3_client)

    with pytest.raises(Exception):
        aws.get_json_data(test_bucket, test_key)
    stubber.assert_no_pending_responses()


def test_get_json_data_default_nonexisting(mocker):
    s3_client = boto3.client("s3")
    stubber = botocore.stub.Stubber(s3_client)

    test_key = "data.json"
    test_bucket = "test-bucket"
    test_data = {
        "foo": "bar"
    }

    stubber.add_client_error(
        "get_object",
        service_error_code="NoSuchKey",
        expected_params={
            "Bucket": test_bucket,
            "Key": test_key,
        },
    )
    stubber.activate()
    mocker.patch("boto3.client", lambda service: s3_client)

    res = aws.get_json_data(test_bucket, test_key, test_data)
    stubber.assert_no_pending_responses()
    assert res == test_data
