from moodlecli import utils, moodle
import pytest
import json
import csv
from click.testing import CliRunner
from moodlecli.main import cli
import boto3
import botocore.stub

TEST_MOODLE_URL = "http://test-things"
TEST_MOODLE_TOKEN = "e4586db9345084f15abc7326b84dde21"
TEST_ENV = {"MOODLE_URL": TEST_MOODLE_URL, "MOODLE_TOKEN": TEST_MOODLE_TOKEN}


@pytest.fixture
def moodle_requests_mock(requests_mock):
    def get_matching_helper(request, context):
        wsfunction = request.qs["wsfunction"][0]

        if wsfunction == moodle.MOODLE_FUNC_GRADEREPORT_USER_GET_GRADE_ITEMS:
            return {
                "usergrades": [
                    {
                        "userid": 11,
                        "gradeitems": [
                            {"iteminstance": 22, "gradedatesubmitted": 33}
                        ]
                    }
                ]
            }
        elif wsfunction == moodle.MOODLE_FUNC_GET_USER_QUIZ_ATTEMPTS:
            return {
                "attempts": [
                    {
                        "id": 101,
                        "attempt": 1,
                        "gradednotificationsenttime": 22
                    },
                    {
                        "id": 102,
                        "attempt": 2,
                        "gradednotificationsenttime": 33
                    }
                ]
            }
        elif wsfunction == moodle.MOODLE_FUNC_GET_QUIZ_ATTEMPT:
            return {"attempt": {}, "questions": []}
        elif wsfunction == moodle.MOODLE_FUNC_GET_QUIZZES_BY_COURSES:
            return {"quizzes": [{"name": "Quiz 1", "sumgrades": 10}]}
        else:
            raise Exception("Unexpected call to Moodle requests mock")

    requests_mock.get(f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
                      json=get_matching_helper)


@pytest.fixture
def moodle_mock(mocker):
    moodle = mocker.Mock()
    moodle.get_grades_by_course = mocker.Mock(
        return_value={
            "usergrades": [
                {
                    "userid": 11,
                    "gradeitems": [
                        {"iteminstance": 22, "gradedatesubmitted": 33}
                    ]
                }
            ]
        }
    )
    moodle.get_quizzes_by_courses = mocker.Mock(
        return_value={"quizzes": [{"name": "Quiz 1", "sumgrades": 10}]}
    )
    moodle.get_user_quiz_attempts = mocker.Mock(
        return_value={
            "attempts": [
                {"id": 101, "attempt": 1, "gradednotificationsenttime": 22},
                {"id": 102, "attempt": 2, "gradednotificationsenttime": 33}
            ]
        }
    )
    moodle.get_quiz_attempt_details = mocker.Mock(
        return_value={"attempt": {}, "questions": []}
    )
    return moodle


def test_update_grades_data_empty_cache(moodle_mock):

    res = utils.update_grades_data(moodle_mock, 10, {})

    moodle_mock.get_grades_by_course.assert_called_once_with(10)
    moodle_mock.get_quizzes_by_courses.assert_called_once_with([10])
    moodle_mock.get_user_quiz_attempts.assert_called_once_with("11", "22")
    assert moodle_mock.get_quiz_attempt_details.call_count == 2
    moodle_mock.get_quiz_attempt_details.assert_any_call("101")
    moodle_mock.get_quiz_attempt_details.assert_any_call("102")
    assert res == {
        "usergrades": [
            {
                "userid": 11,
                "gradeitems": [
                    {"iteminstance": 22, "gradedatesubmitted": 33}
                ]
            }
        ],
        "quizzes": [{"name": "Quiz 1", "sumgrades": 10}],
        "attempts": {
            "11": {
                "22": {
                    "summaries": [
                        {
                            "id": 101,
                            "attempt": 1,
                            "gradednotificationsenttime": 22
                        },
                        {
                            "id": 102,
                            "attempt": 2,
                            "gradednotificationsenttime": 33
                        }
                    ],
                    "details": {
                        "101": {"attempt": {}, "questions": []},
                        "102": {"attempt": {}, "questions": []}
                    }
                }
            }
        }
    }


def test_update_grades_data_latest_cache(moodle_mock):
    res = utils.update_grades_data(
        moodle_mock,
        10,
        {
            "usergrades": [
                {
                    "userid": 11,
                    "gradeitems": [
                        {"iteminstance": 22, "gradedatesubmitted": 33}
                    ]
                }
            ],
            "quizzes": [{"name": "Quiz 1", "sumgrades": 10}],
            "attempts": {
                "11": {
                    "22": {
                        "summaries": [
                            {
                                "id": 101,
                                "attempt": 1,
                                "gradednotificationsenttime": 22
                            },
                            {
                                "id": 102,
                                "attempt": 2,
                                "gradednotificationsenttime": 33
                            }
                        ],
                        "details": {
                            "101": {"attempt": {}, "questions": []},
                            "102": {"attempt": {}, "questions": []}
                        }
                    }
                }
            }
        }
    )

    moodle_mock.get_grades_by_course.assert_called_once_with(10)
    moodle_mock.get_quizzes_by_courses.assert_called_once_with([10])
    moodle_mock.get_user_quiz_attempts.assert_not_called()
    moodle_mock.get_quiz_attempt_details.assert_not_called()
    assert res == {
        "usergrades": [
            {
                "userid": 11,
                "gradeitems": [
                    {"iteminstance": 22, "gradedatesubmitted": 33}
                ]
            }
        ],
        "quizzes": [{"name": "Quiz 1", "sumgrades": 10}],
        "attempts": {
            "11": {
                "22": {
                    "summaries": [
                        {
                            "id": 101,
                            "attempt": 1,
                            "gradednotificationsenttime": 22
                        },
                        {
                            "id": 102,
                            "attempt": 2,
                            "gradednotificationsenttime": 33
                        }
                    ],
                    "details": {
                        "101": {"attempt": {}, "questions": []},
                        "102": {"attempt": {}, "questions": []}
                    }
                }
            }
        }
    }


def test_update_grades_data_stale_cache(moodle_mock):
    res = utils.update_grades_data(
        moodle_mock,
        10,
        {
            "usergrades": [
                {
                    "userid": 11,
                    "gradeitems": [
                        {"iteminstance": 22, "gradedatesubmitted": 22}
                    ]
                }
            ],
            "quizzes": [{"name": "Quiz 1", "sumgrades": 10}],
            "attempts": {
                "11": {
                    "22": {
                        "summaries": [
                            {
                                "id": 101,
                                "attempt": 1,
                                "gradednotificationsenttime": 22
                            }
                        ],
                        "details": {
                            "101": {"attempt": {}, "questions": []}
                        }
                    }
                }
            }
        }
    )

    moodle_mock.get_grades_by_course.assert_called_once_with(10)
    moodle_mock.get_quizzes_by_courses.assert_called_once_with([10])
    moodle_mock.get_user_quiz_attempts.assert_called_once_with("11", "22")
    assert moodle_mock.get_quiz_attempt_details.call_count == 1
    moodle_mock.get_quiz_attempt_details.assert_called_once_with("102")
    assert res == {
        "usergrades": [
            {
                "userid": 11,
                "gradeitems": [
                    {"iteminstance": 22, "gradedatesubmitted": 33}
                ]
            }
        ],
        "quizzes": [{"name": "Quiz 1", "sumgrades": 10}],
        "attempts": {
            "11": {
                "22": {
                    "summaries": [
                        {
                            "id": 101,
                            "attempt": 1,
                            "gradednotificationsenttime": 22
                        },
                        {
                            "id": 102,
                            "attempt": 2,
                            "gradednotificationsenttime": 33
                        }
                    ],
                    "details": {
                        "101": {"attempt": {}, "questions": []},
                        "102": {"attempt": {}, "questions": []}
                    }
                }
            }
        }
    }


def test_export_grades(moodle_requests_mock, tmp_path, mocker):
    runner = CliRunner()

    s3_client = boto3.client("s3")
    stubber = botocore.stub.Stubber(s3_client)

    test_key = "/grades/course1.json"
    test_bucket = "test-bucket"

    stubber.add_client_error(
        "get_object",
        service_error_code="NoSuchKey",
        expected_params={
            "Bucket": test_bucket,
            "Key": test_key,
        },
    )

    expected_put_data = {
        "usergrades": [
            {
                "userid": 11,
                "gradeitems": [
                    {"iteminstance": 22, "gradedatesubmitted": 33}
                ]
            }
        ],
        "quizzes": [{"name": "Quiz 1", "sumgrades": 10}],
        "attempts": {
            "11": {
                "22": {
                    "summaries": [
                        {
                            "id": 101,
                            "attempt": 1,
                            "gradednotificationsenttime": 22
                        },
                        {
                            "id": 102,
                            "attempt": 2,
                            "gradednotificationsenttime": 33
                        }
                    ],
                    "details": {
                        "101": {"attempt": {}, "questions": []},
                        "102": {"attempt": {}, "questions": []}
                    }
                }
            }
        }
    }

    expected_params = {
        "Bucket": test_bucket,
        "Body": json.dumps(expected_put_data).encode("utf-8"),
        "Key": test_key
    }
    stubber.add_response("put_object", {}, expected_params)
    stubber.activate()
    mocker.patch("boto3.client", lambda service: s3_client)

    result = runner.invoke(
        cli,
        ["export-grades", "21", test_bucket, test_key],
        env=TEST_ENV
    )

    assert result.exit_code == 0
    stubber.assert_no_pending_responses()


def test_export_bulk_grades(moodle_requests_mock, tmp_path, mocker):
    runner = CliRunner()

    s3_client = boto3.client("s3")
    stubber = botocore.stub.Stubber(s3_client)

    test_bucket = "test-bucket"

    stubber.add_client_error(
        "get_object",
        service_error_code="NoSuchKey",
        expected_params={
            "Bucket": test_bucket,
            "Key": "s3grades/1.json",
        },
    )

    expected_put_data = {
        "usergrades": [
            {
                "userid": 11,
                "gradeitems": [
                    {"iteminstance": 22, "gradedatesubmitted": 33}
                ]
            }
        ],
        "quizzes": [{"name": "Quiz 1", "sumgrades": 10}],
        "attempts": {
            "11": {
                "22": {
                    "summaries": [
                        {
                            "id": 101,
                            "attempt": 1,
                            "gradednotificationsenttime": 22
                        },
                        {
                            "id": 102,
                            "attempt": 2,
                            "gradednotificationsenttime": 33
                        }
                    ],
                    "details": {
                        "101": {"attempt": {}, "questions": []},
                        "102": {"attempt": {}, "questions": []}
                    }
                }
            }
        }
    }

    expected_params = {
        "Bucket": test_bucket,
        "Body": json.dumps(expected_put_data).encode("utf-8"),
        "Key": "s3grades/1.json"
    }
    stubber.add_response("put_object", {}, expected_params)
    stubber.activate()
    mocker.patch("boto3.client", lambda service: s3_client)

    with runner.isolated_filesystem(temp_dir=tmp_path):

        with open("courses.csv", "w") as f:
            writer = csv.DictWriter(
                f,
                utils.bulk_export_csv_course_ids()
            )
            writer.writeheader()
            writer.writerows([{utils.CSV_COURSE_ID: 1}])

        result_grades = runner.invoke(
            cli,
            ["export-bulk", "courses.csv", test_bucket, "s3grades", "grades"],
            env=TEST_ENV
        )

        assert result_grades.exit_code == 0
        stubber.assert_no_pending_responses()
