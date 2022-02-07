from urllib import parse
from moodlecli import utils, moodle
import pytest
import os
import json
import csv
from click.testing import CliRunner
from moodlecli.main import cli

TEST_MOODLE_URL = "http://test-things"
TEST_MOODLE_TOKEN = "e4586db9345084f15abc7326b84dde21"
TEST_ENV = {'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN}


@pytest.fixture
def moodle_requests_mock(requests_mock):
    def get_matching_helper(request, context):
        wsfunction = request.qs["wsfunction"][0]

        if wsfunction == moodle.MOODLE_FUNC_GET_ROLE_BY_SHORTNAME:
            return {'id': 2}
        elif wsfunction == moodle.MOODLE_FUNC_GET_USERS:
            # Used to exercise error in course_bulk_setup
            if request.qs["criteria[0][value]"][0] == 'invalid@gmail.com':
                return {'exception': 'value'}
            else:
                return {'users': [{'id': 2}]}
        elif wsfunction == moodle.MOODLE_FUNC_GET_SELF_ENROLMENT_METHODS:
            return [{'id': 2}]
        else:
            return []

    def post_matching_helper(request, context):

        wsfunction = parse.parse_qs(request.body)['wsfunction'][0]

        if wsfunction == moodle.MOODLE_FUNC_DUPLICATE_COURSE:
            return {'id': 3}
        elif wsfunction == moodle.MOODLE_FUNC_ENABLE_SELF_ENROLMENT_METHOD:
            return {'id': 2}
        elif wsfunction == moodle.MOODLE_FUNC_CREATE_USERS:
            return {'users': {'id': 5}}
        elif wsfunction == moodle.MOODLE_FUNC_IMPORT_COURSE:
            return {'id': 3}
        elif wsfunction == moodle.MOODLE_FUNC_SET_SELF_ENROLMENT_METHOD_KEY:
            return {'id': 3}
        else:
            return []

    requests_mock.get(f'{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}',
                      json=get_matching_helper)
    requests_mock.post(f'{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}',
                       json=post_matching_helper)


def test_copy_course(moodle_requests_mock):
    runner = CliRunner()

    result = runner.invoke(cli, ['copy-course', '3', 'Algebra3', 'ALG3', '1'],
                           env=TEST_ENV)
    assert result.exit_code == 0


def test_course_bulk_csv(requests_mock, tmp_path):
    test_json = {'foo': 'bar'}
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        requests_mock.get(f'{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}',
                          json=test_json)

        result = runner.invoke(cli, ['course-bulk-csv', 'output.csv'],
                               env=TEST_ENV)
        assert result.exit_code == 0
        assert os.stat("output.csv").st_size != 0


def test_course_bulk_setup(moodle_requests_mock, tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):

        with open('test.csv', 'w') as f:
            writer = csv.DictWriter(
                    f,
                    utils.course_bulk_input_csv_fieldnames()
                )
            writer.writeheader()
            writer.writerows([{utils.CSV_INST_FNAME: 'Tom',
                               utils.CSV_INST_LNAME: 'Michaels',
                               utils.CSV_INST_EMAIL: 'tommichaels@gmail.com',
                               utils.CSV_INST_AUTH: 'manual',
                               utils.CSV_COURSE_NAME: 'Algebra',
                               utils.CSV_COURSE_SHORTNAME: 'a1',
                               utils.CSV_COURSE_CATEGORY: 'MISC'},
                              {utils.CSV_INST_FNAME: 'Christy',
                               utils.CSV_INST_LNAME: 'Yolanda',
                               utils.CSV_INST_EMAIL: 'christy@gmail.com',
                               utils.CSV_INST_AUTH: 'manual',
                               utils.CSV_COURSE_NAME: 'English',
                               utils.CSV_COURSE_SHORTNAME: 'e1',
                               utils.CSV_COURSE_CATEGORY: 'MISC'}])

        result = runner.invoke(cli, ['course-bulk-setup',
                                     '2', 'test.csv', 'output.csv'],
                               env=TEST_ENV)

        assert result.exit_code == 0
        assert os.stat("output.csv").st_size != 0
        with open('output.csv', 'r') as f:
            assert len(list(csv.DictReader(f))) == 2


def test_courses(requests_mock):
    test_json = {"foo": "bar"}
    runner = CliRunner()
    requests_mock.get(f'{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}',
                      json=test_json)

    result = runner.invoke(cli, ['courses'],
                           env=TEST_ENV)
    assert result.exit_code == 0
    assert json.loads(result.output) == test_json


def test_enable_self_enrolment_method(moodle_requests_mock):
    runner = CliRunner()

    result = runner.invoke(cli, ['enable-self-enrolment-method', '3'],
                           env=TEST_ENV)
    assert result.exit_code == 0


def test_enrol_bulk(moodle_requests_mock, tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):

        with open('students.csv', 'w') as f:
            writer = csv.DictWriter(
                    f,
                    utils.enrol_bulk_input_csv_fieldnames()
                )
            writer.writeheader()
            writer.writerows([{utils.CSV_USER_FNAME: 'Tom',
                               utils.CSV_USER_LNAME: 'Michaels',
                               utils.CSV_USER_EMAIL: 'tommichaels@gmail.com',
                               utils.CSV_USER_AUTH: 'manual'},
                              {utils.CSV_USER_FNAME: 'Phil',
                               utils.CSV_USER_LNAME: 'Thomas',
                               utils.CSV_USER_EMAIL: 'philthomas@gmail.com',
                               utils.CSV_USER_AUTH: 'manual'}])

        result = runner.invoke(cli, ['enrol-bulk',
                                     '3', 'student', 'students.csv'],
                               env=TEST_ENV)
        assert result.exit_code == 0


def test_enrol_bulk_csv(requests_mock, tmp_path):
    test_json = {'foo': 'bar'}
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        requests_mock.get(f'{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}',
                          json=test_json)

        result = runner.invoke(cli, ['enrol-bulk-csv', 'output.csv'],
                               env=TEST_ENV)
        assert result.exit_code == 0
        assert os.stat("output.csv").st_size != 0


def test_import_bulk_csv(requests_mock, tmp_path):
    test_json = {'foo': 'bar'}
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        requests_mock.get(f'{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}',
                          json=test_json)

        result = runner.invoke(cli, ['import-bulk-csv', 'output.csv'],
                               env=TEST_ENV)
        assert result.exit_code == 0
        assert os.stat("output.csv").st_size != 0


def test_import_bulk(moodle_requests_mock, tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):

        with open('target_courses.csv', 'w') as f:
            writer = csv.DictWriter(
                    f,
                    utils.import_bulk_input_csv_fieldnames()
                )
            writer.writeheader()
            writer.writerows([{utils.CSV_COURSE_ID: 3},
                              {utils.CSV_COURSE_ID: 1}])

        result = runner.invoke(cli, ['import-bulk', '2', 'target_courses.csv'],
                               env=TEST_ENV)
        assert result.exit_code == 0


def test_import_course(moodle_requests_mock, tmp_path):
    runner = CliRunner()

    result = runner.invoke(cli, ['import-course', '2', '3'],
                           env=TEST_ENV)
    assert result.exit_code == 0


def test_role_info(requests_mock):
    test_json = {"foo": "bar"}
    runner = CliRunner()
    requests_mock.get(f'{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}',
                      json=test_json)

    result = runner.invoke(cli, ['role-info', 'editingteacher'],
                           env=TEST_ENV)
    assert result.exit_code == 0
    assert json.loads(result.output) == test_json


def test_self_enrollment_methods(moodle_requests_mock):
    runner = CliRunner()

    result = runner.invoke(cli, ['self-enrolment-methods',
                                 '2', '3'],
                           env=TEST_ENV)
    assert result.exit_code == 0


def test_set_self_enrolment_method_key(moodle_requests_mock):
    runner = CliRunner()

    result = runner.invoke(cli, ['set-self-enrolment-method-key',
                                 '2', 'abc123'],
                           env=TEST_ENV)
    assert result.exit_code == 0


def test_course_bulk_setup_error(moodle_requests_mock, tmp_path):
    """This exercises an error that can be caused by invalid email inputs
    in the course-bulk-setup CLI command"""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):

        with open('test.csv', 'w') as f:
            writer = csv.DictWriter(
                    f,
                    utils.course_bulk_input_csv_fieldnames()
                )
            writer.writeheader()
            writer.writerows([{utils.CSV_INST_FNAME: 'Tom',
                               utils.CSV_INST_LNAME: 'Michaels',
                               utils.CSV_INST_EMAIL: 'tommichaels@gmail.com',
                               utils.CSV_INST_AUTH: 'manual',
                               utils.CSV_COURSE_NAME: 'Algebra',
                               utils.CSV_COURSE_SHORTNAME: 'a1',
                               utils.CSV_COURSE_CATEGORY: 'MISC'},
                              {utils.CSV_INST_FNAME: 'Aliza',
                               utils.CSV_INST_LNAME: 'Brown',
                               utils.CSV_INST_EMAIL: 'invalid@gmail.com',
                               utils.CSV_INST_AUTH: 'manual',
                               utils.CSV_COURSE_NAME: 'English',
                               utils.CSV_COURSE_SHORTNAME: 'e1',
                               utils.CSV_COURSE_CATEGORY: 'MISC'}])

        # with pytest.raises(Exception, match="value"):
        result = runner.invoke(cli, ['course-bulk-setup',
                                     '2', 'test.csv', 'output.csv'],
                               env=TEST_ENV)

        # Add CSV dictreader check here
        assert result.exit_code == 1
        assert result.exception is not None
        assert os.stat("output.csv").st_size != 0

        with open('output.csv', 'r') as f:
            assert len(list(csv.DictReader(f))) == 1
