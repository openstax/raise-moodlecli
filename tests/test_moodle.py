import pytest
from moodlecli import moodle
from moodlecli import utils
import random
from requests.exceptions import ConnectionError

TEST_MOODLE_URL = "http://dagobah"
TEST_MOODLE_TOKEN = "1234"


def test_convert_moodle_params():
    cases = [
        {
            "input": {"a": 1, "b": 2},
            "expected": {"a": 1, "b": 2}
        },
        {
            "input": {"foo": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]},
            "expected": {
                "foo[0][a]": 1,
                "foo[0][b]": 2,
                "foo[1][a]": 3,
                "foo[1][b]": 4,
            }
        }
    ]
    for case in cases:
        assert moodle.convert_moodle_params(case["input"]) == case["expected"]


def test_copy_course(mocker):
    session_mock = mocker.Mock()
    session_mock.post.return_value.json.return_value = {}
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.copy_course(
        1,
        "Long name",
        "Short name",
        2,
        True
    )
    session_mock.post.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        {
            "courseid": 1,
            "fullname": "Long name",
            "shortname": "Short name",
            "categoryid": 2,
            "options[0][name]": "users",
            "options[0][value]": "1",
            "wsfunction": moodle.MOODLE_FUNC_DUPLICATE_COURSE,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )


def test_import_course(mocker):
    session_mock = mocker.Mock()
    session_mock.post.return_value.json.return_value = {}

    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.import_course(11, 12)
    session_mock.post.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        {
            "importfrom": 11,
            "importto": 12,
            "wsfunction": moodle.MOODLE_FUNC_IMPORT_COURSE,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )


def test_get_courses(mocker):
    session_mock = mocker.Mock()
    session_mock.get.return_value.json.return_value = {}
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.get_courses()
    session_mock.get.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        params={
            "wsfunction": moodle.MOODLE_FUNC_GET_COURSES,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )


def test_get_courses_by_shortname(mocker):
    session_mock = mocker.Mock()
    session_mock.get.return_value.json.return_value = {}
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.get_course_by_shortname('example')
    session_mock.get.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        params={
            "wsfunction": moodle.MOODLE_FUNC_GET_COURSES_BY_FIELD,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN,
            'field': 'shortname',
            'value': 'example'
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )


def test_get_self_enrolment_methods(mocker):
    session_mock = mocker.Mock()
    session_mock.get.return_value.json.return_value = {}
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.get_self_enrolment_methods(111, 12)
    session_mock.get.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        params={
            "courseid": 111,
            "roleid": 12,
            "wsfunction": moodle.MOODLE_FUNC_GET_SELF_ENROLMENT_METHODS,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )


def test_get_role_by_shortname(mocker):
    session_mock = mocker.Mock()
    session_mock.get.return_value.json.return_value = {}
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.get_role_by_shortname("rolename")
    session_mock.get.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        params={
            "shortname": "rolename",
            "wsfunction": moodle.MOODLE_FUNC_GET_ROLE_BY_SHORTNAME,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )


def test_enable_self_enrolment_method(mocker):
    session_mock = mocker.Mock()
    session_mock.post.return_value.json.return_value = {}
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.enable_self_enrolment_method(111)
    session_mock.post.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        {
            "enrolid": 111,
            "wsfunction": moodle.MOODLE_FUNC_ENABLE_SELF_ENROLMENT_METHOD,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )


def test_set_self_enrolment_method_key(mocker):
    session_mock = mocker.Mock()
    session_mock.post.return_value.json.return_value = {}
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.set_self_enrolment_method_key(111, "Enrolment key value")
    session_mock.post.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        {
            "enrolid": 111,
            "enrolkey": "Enrolment key value",
            "wsfunction": moodle.MOODLE_FUNC_SET_SELF_ENROLMENT_METHOD_KEY,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )


def test_get_user_by_email(mocker):
    session_mock = mocker.Mock()
    user_data = {"id": 111}
    session_mock.get.return_value.json.return_value = {
        "users": [user_data]
    }
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    res = client.get_user_by_email("admin@acmeinc.com")
    session_mock.get.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        params={
            "criteria[0][key]": "email",
            "criteria[0][value]": "admin@acmeinc.com",
            "wsfunction": moodle.MOODLE_FUNC_GET_USERS,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )
    assert res == user_data

    # Check empty result path
    session_mock.get.return_value.json.return_value = {
        "users": []
    }
    res = client.get_user_by_email("admin@acmeinc.com")
    assert res is None

    # Check multiple users error path
    session_mock.get.return_value.json.return_value = {
        "users": [user_data, user_data]
    }

    with pytest.raises(Exception, match="Multiple users returned with email"):
        client.get_user_by_email("admin@acmeinc.com")


def test_create_user(mocker):
    session_mock = mocker.Mock()
    session_mock.post.return_value.json.return_value = [{}]
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.create_user("fname", "lname", "email", "oauth2")
    session_mock.post.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        {
            "users[0][username]": "email",
            "users[0][email]": "email",
            "users[0][firstname]": "fname",
            "users[0][lastname]": "lname",
            "users[0][auth]": "oauth2",
            "wsfunction": moodle.MOODLE_FUNC_CREATE_USERS,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )

    # Check that password is included for manual auth
    client.create_user("fname", "lname", "email", "manual")
    assert "users[0][password]" in session_mock.post.call_args[0][1]


def test_create_user_capital_email(mocker):
    session_mock = mocker.Mock()
    session_mock.post.return_value.json.return_value = [{}]
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.create_user("fname", "lname", "EMAIL", "oauth2")
    session_mock.post.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        {
            "users[0][username]": "email",
            "users[0][email]": "email",
            "users[0][firstname]": "fname",
            "users[0][lastname]": "lname",
            "users[0][auth]": "oauth2",
            "wsfunction": moodle.MOODLE_FUNC_CREATE_USERS,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )


def test_get_course_enrolment_url(mocker):
    session_mock = mocker.Mock()
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    enrol_url = client.get_course_enrolment_url(111)
    assert enrol_url == f"{TEST_MOODLE_URL}/enrol/index.php?id=111"


def test_enrol_user(mocker):
    session_mock = mocker.Mock()
    session_mock.post.return_value.json.return_value = [{}]
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.enrol_user(1, 2, 3)
    session_mock.post.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        {
            "enrolments[0][courseid]": 1,
            "enrolments[0][userid]": 2,
            "enrolments[0][roleid]": 3,
            "wsfunction": moodle.MOODLE_FUNC_ENROL_USER,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )


def test_unenrol_user(mocker):
    session_mock = mocker.Mock()
    session_mock.post.return_value.json.return_value = [{}]
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.unenrol_user(1, 2)
    session_mock.post.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        {
            "enrolments[0][courseid]": 1,
            "enrolments[0][userid]": 2,
            "wsfunction": moodle.MOODLE_FUNC_UNENROL_USER,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )


def test_setup_duplicate_course(mocker):
    random.seed(1)
    moodle_mock = mocker.Mock()
    course_data = {
        utils.CSV_INST_FNAME: "fname",
        utils.CSV_INST_LNAME: "lname",
        utils.CSV_INST_EMAIL: "fname@lname.com",
        utils.CSV_INST_AUTH: "oauth2",
        utils.CSV_COURSE_NAME: "test course",
        utils.CSV_COURSE_SHORTNAME: "testcourse",
        utils.CSV_COURSE_CATEGORY: 1
    }
    moodle_mock.get_user_by_email.return_value = None
    moodle_mock.create_user.return_value = {"id": "userid"}
    moodle_mock.copy_course.return_value = {"id": "courseid"}
    moodle_mock.get_self_enrolment_methods.return_value = [{"id": "enrolid"}]
    moodle_mock.get_course_enrolment_url.return_value = "enrolmenturl"

    res = utils.setup_duplicate_course(
        moodle_mock,
        111,
        course_data,
        1,
        2
    )

    moodle_mock.create_user.assert_called_once_with(
        "fname", "lname", "fname@lname.com", "oauth2"
    )
    moodle_mock.copy_course.assert_called_once_with(
        111, "test course", "testcourse", 1
    )
    moodle_mock.enrol_user.assert_called_once_with(
        "courseid",
        "userid",
        1
    )
    moodle_mock.enable_self_enrolment_method.assert_called_once_with("enrolid")
    moodle_mock.set_self_enrolment_method_key.assert_called_once()
    assert moodle_mock.set_self_enrolment_method_key.call_args.args[0] == \
        "enrolid"
    assert res[utils.CSV_COURSE_ID] == "courseid"
    assert res[utils.CSV_COURSE_ENROLMENT_URL] == "enrolmenturl"
    assert res[utils.CSV_COURSE_ENROLMENT_KEY] == "suave-spider-1033"


def test_setup_duplicate_course_timeout_workaround(mocker):
    random.seed(1)
    mocker.patch(
        "moodlecli.utils.sleep",
        lambda x: None
    )
    moodle_mock = mocker.Mock()
    course_data = {
        utils.CSV_INST_FNAME: "fname",
        utils.CSV_INST_LNAME: "lname",
        utils.CSV_INST_EMAIL: "fname@lname.com",
        utils.CSV_INST_AUTH: "oauth2",
        utils.CSV_COURSE_NAME: "test course",
        utils.CSV_COURSE_SHORTNAME: "testcourse",
        utils.CSV_COURSE_CATEGORY: 1
    }
    moodle_mock.get_user_by_email.return_value = None
    moodle_mock.create_user.return_value = {"id": "userid"}
    moodle_mock.copy_course.side_effect = ConnectionError("Mock timeout")
    moodle_mock.get_course_by_shortname.side_effect = [
        {'courses': []},
        {'courses': [{"shortname": "testcourse", "id": "courseid"}]},
    ]
    moodle_mock.get_self_enrolment_methods.return_value = [{"id": "enrolid"}]
    moodle_mock.get_course_enrolment_url.return_value = "enrolmenturl"

    res = utils.setup_duplicate_course(
        moodle_mock,
        111,
        course_data,
        1,
        2
    )

    moodle_mock.create_user.assert_called_once_with(
        "fname", "lname", "fname@lname.com", "oauth2"
    )
    moodle_mock.copy_course.assert_called_once_with(
        111, "test course", "testcourse", 1
    )
    moodle_mock.enrol_user.assert_called_once_with(
        "courseid",
        "userid",
        1
    )
    moodle_mock.enable_self_enrolment_method.assert_called_once_with("enrolid")
    moodle_mock.set_self_enrolment_method_key.assert_called_once()
    assert moodle_mock.set_self_enrolment_method_key.call_args.args[0] == \
        "enrolid"
    assert res[utils.CSV_COURSE_ID] == "courseid"
    assert res[utils.CSV_COURSE_ENROLMENT_URL] == "enrolmenturl"
    assert res[utils.CSV_COURSE_ENROLMENT_KEY] == "suave-spider-1033"


def test_check_for_moodle_error(mocker):
    result_mock = mocker.Mock()
    result_mock.json.return_value = {
        "exception": "error"
    }

    with pytest.raises(Exception):
        moodle.check_for_moodle_error(result_mock)

    # Confirm we handle valid array responses without errors
    result_mock.json.return_value = []
    moodle.check_for_moodle_error(result_mock)


def test_get_course_grades(mocker):
    session_mock = mocker.Mock()
    session_mock.get.return_value.json.return_value = [{}]
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    grades_json = client.get_grades_by_course(2)

    session_mock.get.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        params={
            "courseid": 2,
            "wsfunction": moodle.MOODLE_FUNC_GRADEREPORT_USER_GET_GRADE_ITEMS,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )

    assert grades_json == [{}]


def test_get_users_by_course(mocker):
    session_mock = mocker.Mock()
    session_mock.get.return_value.json.return_value = [{}]
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    users_json = client.get_users_by_course(2)

    session_mock.get.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        params={
            "courseid": 2,
            "wsfunction": moodle.MOODLE_FUNC_CORE_ENROL_GET_ENROLLED_USERS,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )

    assert users_json == [{}]


def test_get_user_uuids(mocker):
    session_mock = mocker.Mock()
    session_mock.get.return_value.json.return_value = [{}]
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.get_user_uuids()
    session_mock.get.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        params={
            "wsfunction": moodle.MOODLE_FUNC_GET_USER_UUIDS,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )


def test_get_inidividual_user_uuids(mocker):
    session_mock = mocker.Mock()
    session_mock.get.return_value.json.return_value = [{}]
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.get_user_uuids([1, 2])
    print(session_mock.get.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        params={
            "wsfunction": moodle.MOODLE_FUNC_GET_USER_UUIDS,
            "user_ids[0][id]": 1,
            "user_ids[1][id]": 2,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    ))


def test_get_quizzes_by_courses(mocker):
    session_mock = mocker.Mock()
    session_mock.get.return_value.json.return_value = [{}]
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.get_quizzes_by_courses([1, 2])
    print(session_mock.get.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        params={
            "wsfunction": moodle.MOODLE_FUNC_GET_QUIZZES_BY_COURSES,
            "courseids[0]": 1,
            "courseids[1]": 2,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    ))


def test_get_user_quiz_attempts(mocker):
    session_mock = mocker.Mock()
    session_mock.get.return_value.json.return_value = [{}]
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.get_user_quiz_attempts(11, 22)
    print(session_mock.get.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        params={
            "wsfunction": moodle.MOODLE_FUNC_GET_USER_QUIZ_ATTEMPTS,
            "userid": 11,
            "quizid": 22,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    ))


def test_get_quiz_attempt_details(mocker):
    session_mock = mocker.Mock()
    session_mock.get.return_value.json.return_value = [{}]
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )
    client.get_quiz_attempt_details(11)
    print(session_mock.get.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        params={
            "wsfunction": moodle.MOODLE_FUNC_GET_QUIZ_ATTEMPT,
            "attemptid": 11,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN
        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    ))


def test_get_policy_acceptance_data(mocker):
    policyversionid = 1
    user_ids = [1, 2, 3]
    session_mock = mocker.Mock()
    session_mock.get.return_value.json.return_value = [{}]
    client = moodle.MoodleClient(
        session_mock, TEST_MOODLE_URL, TEST_MOODLE_TOKEN
    )

    client.get_policy_acceptance_data(policyversionid, user_ids)

    client.session.get.assert_called_once_with(
        f"{TEST_MOODLE_URL}{moodle.MOODLE_WEBSERVICE_PATH}",
        params={
            "wsfunction": moodle.MOODLE_FUNC_GET_POLICY_ACCEPTANCE_DATA,
            "policyversionid": policyversionid,
            "user_ids[0]": 1,
            "user_ids[1]": 2,
            "user_ids[2]": 3,
            "moodlewsrestformat": "json",
            "wstoken": TEST_MOODLE_TOKEN

        },
        timeout=moodle.MOODLE_REQUEST_TIMEOUT
    )
