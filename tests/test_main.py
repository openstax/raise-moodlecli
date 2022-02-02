from urllib import request, parse

import pytest
from moodlecli import main, utils, moodle
import requests
import requests_mock as rm
import os
import json
import csv



from click.testing import CliRunner
from moodlecli.main import cli

# TEST_MOODLE_URL = "http://dagobah"
# TEST_MOODLE_TOKEN = "1234"

TEST_MOODLE_URL = "http://localhost:8000"
TEST_MOODLE_TOKEN = "94f9362009170815d912b149bc1e5ffa"

MOODLE_WEBSERVICE_PATH = "/webservice/rest/server.php"


def get_matching_helper(request, context):
    print("GET_HELPER: ", request.qs)

    wsfunction =  request.qs["wsfunction"][0]

    if wsfunction == moodle.MOODLE_FUNC_GET_ROLE_BY_SHORTNAME:
        return {'id': 2}
    elif wsfunction == moodle.MOODLE_FUNC_GET_USERS:
        #if the criteria - if its this function and - the value from CSV is your 'invalid' one 
        if request.qs["criteria[0][value]"][0] == 'invalid@gmail.com':
            return {'exception': 'value'}
        else:
            return {'users': [{'id': 2}]}
    elif wsfunction == moodle.MOODLE_FUNC_GET_SELF_ENROLMENT_METHODS:
        return [{'id': 2}]
    else:
        return []

def post_matching_helper(request, context):
    print("POST_HELPER: ", parse.parse_qs(request.body))

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





def test_copy_course(requests_mock):
    runner = CliRunner()
    requests_mock.post(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=post_matching_helper)
    # copy-course <SOURCE_ID> <COURSE_NAME> <COURSE_SHORT_NAME> <COURSE_CATEGORY_ID>
    print("MOCK CREATED")
    result = runner.invoke(cli, ['copy-course', '3', 'Algebra3', 'ALG3', '1'], env={'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN})
    assert result.exit_code == 0
    print(result.output)

def test_course_bulk_csv(requests_mock, tmp_path):
    test_json = {'foo': 'bar'}
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path): 
        requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=test_json)
        # course-bulk-csv  <OUTPUT_CSV>
        result = runner.invoke(cli, ['course-bulk-csv', 'output.csv'], env={'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN})
        assert result.exit_code == 0
        assert os.stat("output.csv").st_size != 0


def test_course_bulk_setup(requests_mock, tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):      
        requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=get_matching_helper)
        requests_mock.post(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=post_matching_helper)

        f = open('test.csv', 'w')
        writer = csv.DictWriter(
                f,
                utils.course_bulk_input_csv_fieldnames()
            )
        writer.writeheader()
        writer.writerow({utils.CSV_INST_FNAME:'Tom', utils.CSV_INST_LNAME : 'Michaels', utils.CSV_INST_EMAIL:'tommichaels@gmail.com', utils.CSV_INST_AUTH: 'manual', utils.CSV_COURSE_NAME: 'Algebra', utils.CSV_COURSE_SHORTNAME:'a1', utils.CSV_COURSE_CATEGORY:'MISC'})
        f.close()

        result = runner.invoke(cli,
                        ['course-bulk-setup', '2', 'test.csv', 'output.csv'],
                        env={'MOODLE_URL': TEST_MOODLE_URL, "MOODLE_TOKEN": TEST_MOODLE_TOKEN})

        assert result.exit_code == 0
        assert os.stat("output.csv").st_size != 0

def test_courses(requests_mock):
    test_json = {"foo": "bar"}
    runner = CliRunner()
    requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=test_json)
    # courses
    result = runner.invoke(cli, ['courses'], env={'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN})
    assert result.exit_code == 0
    assert json.loads(result.output) == test_json


def test_enable_self_enrolment_method(requests_mock):
    runner = CliRunner()
    requests_mock.post(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=post_matching_helper)
    # enable-self-enrolment-method <ENROL_ID>
    result = runner.invoke(cli, ['enable-self-enrolment-method', '3'], env={'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN})
    assert result.exit_code == 0

def test_enrol_bulk(requests_mock, tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path): 
        requests_mock.post(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=post_matching_helper)
        requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=get_matching_helper)

        f = open('students.csv', 'w')
        writer = csv.DictWriter(
                f,
                utils.enrol_bulk_input_csv_fieldnames()
            )
        writer.writeheader()
        writer.writerows([{utils.CSV_USER_FNAME:'Tom', utils.CSV_USER_LNAME : 'Michaels', utils.CSV_USER_EMAIL:'tommichaels@gmail.com', utils.CSV_USER_AUTH: 'manual'}, 
                        {utils.CSV_USER_FNAME:'Phil', utils.CSV_USER_LNAME : 'Thomas', utils.CSV_USER_EMAIL:'philthomas@gmail.com', utils.CSV_USER_AUTH: 'manual'}])
        f.close()

        # enrol-bulk <COURSE_ID> <ROLE_SHORTNAME> <USERDATA_CSV>
        result = runner.invoke(cli, ['enrol-bulk', '3', 'student', 'students.csv'], env={'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN})
        assert result.exit_code == 0
        print(result.output)

def test_enrol_bulk_csv(requests_mock, tmp_path):
    test_json = {'foo': 'bar'}
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path): 
        requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=test_json)
        # enrol-bulk-csv  <OUTPUT_CSV>
        result = runner.invoke(cli, ['enrol-bulk-csv', 'output.csv'], env={'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN})
        assert result.exit_code == 0
        assert os.stat("output.csv").st_size != 0

def test_import_bulk_csv(requests_mock, tmp_path):
    test_json = {'foo': 'bar'}
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path): 
        requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=test_json)
        # import-bulk-csv  <OUTPUT_CSV>
        result = runner.invoke(cli, ['import-bulk-csv', 'output.csv'], env={'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN})
        assert result.exit_code == 0
        assert os.stat("output.csv").st_size != 0

# Not sure what import_course returns 
def test_import_bulk(requests_mock, tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path): 
        requests_mock.post(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=post_matching_helper)
        requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=get_matching_helper)

        f = open('target_courses.csv', 'w')
        writer = csv.DictWriter(
                f,
                utils.import_bulk_input_csv_fieldnames()
            )
        writer.writeheader()
        writer.writerows([{utils.CSV_COURSE_ID: 3},
                            {utils.CSV_COURSE_ID: 1}])
        f.close()

        print("INVOKING")
        # import_bulk <SOURCE_COURSE_ID> <TARGET_COURSES_CSV>
        result = runner.invoke(cli, ['import-bulk', '2','target_courses.csv'], env={'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN})
        assert result.exit_code == 0

def test_import_course(requests_mock, tmp_path):
    runner = CliRunner()
    requests_mock.post(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=post_matching_helper)
    # import-course <SOURCE_ID> <TARGET_ID>
    result = runner.invoke(cli, ['import-course', '2', '3'], env={'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN})
    assert result.exit_code == 0
    print(result.output)

def test_role_info(requests_mock):
    test_json = {"foo": "bar"}
    runner = CliRunner()
    requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=test_json)
    # role-info <SHORTNAME>
    result = runner.invoke(cli, ['role-info', 'editingteacher'], env={'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN})
    assert result.exit_code == 0
    assert json.loads(result.output) == test_json
    print(result.output)

def test_self_enrollment_methods(requests_mock):
    runner = CliRunner()
    requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=get_matching_helper)
    # self-enrolment-methods <SOURCE_ID> <TARGET_ID>
    result = runner.invoke(cli, ['self-enrolment-methods', '2', '3'], env={'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN})
    assert result.exit_code == 0
    print(result.output)

def test_set_self_enrolment_method_key(requests_mock):
    runner = CliRunner()
    requests_mock.post(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=post_matching_helper)
    # set-self-enrolment-methods-key <ENROL_ID> <ENROL_KEY>
    result = runner.invoke(cli, ['set-self-enrolment-method-key', '2', 'abc123'], env={'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN})
    assert result.exit_code == 0
    print(result.output)


def test_course_bulk_setup_error(requests_mock, tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):      
        requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=get_matching_helper)
        requests_mock.post(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json=post_matching_helper)

        f = open('test.csv', 'w')
        writer = csv.DictWriter(
                f,
                utils.course_bulk_input_csv_fieldnames()
            )
        writer.writeheader()
        writer.writerows([{utils.CSV_INST_FNAME:'Tom', utils.CSV_INST_LNAME : 'Michaels', 
                        utils.CSV_INST_EMAIL:'tommichaels@gmail.com', utils.CSV_INST_AUTH: 'manual', 
                        utils.CSV_COURSE_NAME: 'Algebra', utils.CSV_COURSE_SHORTNAME:'a1', 
                        utils.CSV_COURSE_CATEGORY:'MISC'},

                        {utils.CSV_INST_FNAME:'Aliza', utils.CSV_INST_LNAME : 'Brown', 
                        utils.CSV_INST_EMAIL:'invalid@gmail.com', utils.CSV_INST_AUTH: 'manual', 
                        utils.CSV_COURSE_NAME: 'English', utils.CSV_COURSE_SHORTNAME:'e1', 
                        utils.CSV_COURSE_CATEGORY:'MISC'}])
        f.close()

        result = runner.invoke(cli,
                        ['course-bulk-setup', '2', 'test.csv', 'output.csv'],
                        env={'MOODLE_URL': TEST_MOODLE_URL, "MOODLE_TOKEN": TEST_MOODLE_TOKEN})

        assert result.exit_code == 0
        assert os.stat("output.csv").st_size != 0
