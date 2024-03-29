from . import utils

MOODLE_WEBSERVICE_PATH = "/webservice/rest/server.php"

MOODLE_FUNC_DUPLICATE_COURSE = "core_course_duplicate_course"
MOODLE_FUNC_GET_COURSES = "core_course_get_courses"
MOODLE_FUNC_GET_COURSES_BY_FIELD = "core_course_get_courses_by_field"
MOODLE_FUNC_IMPORT_COURSE = "core_course_import_course"
MOODLE_FUNC_CORE_ENROL_GET_ENROLLED_USERS = "core_enrol_get_enrolled_users"
MOODLE_FUNC_CREATE_USERS = "core_user_create_users"
MOODLE_FUNC_GET_USERS = "core_user_get_users"
MOODLE_FUNC_ENROL_USER = "enrol_manual_enrol_users"
MOODLE_FUNC_UNENROL_USER = "enrol_manual_unenrol_users"
MOODLE_FUNC_GRADEREPORT_USER_GET_GRADE_ITEMS = \
    "gradereport_user_get_grade_items"
MOODLE_FUNC_ENABLE_SELF_ENROLMENT_METHOD = \
    "local_raisecli_enable_self_enrolment_method"
MOODLE_FUNC_GET_ROLE_BY_SHORTNAME = "local_raisecli_get_role_by_shortname"
MOODLE_FUNC_GET_SELF_ENROLMENT_METHODS = \
    "local_raisecli_get_self_enrolment_methods"
MOODLE_FUNC_GET_USER_UUIDS = "local_raisecli_get_user_uuids"
MOODLE_FUNC_GET_QUIZ_ATTEMPT = "local_raisecli_get_quiz_attempt"
MOODLE_FUNC_SET_SELF_ENROLMENT_METHOD_KEY = \
    "local_raisecli_set_self_enrolment_method_key"
MOODLE_FUNC_GET_QUIZZES_BY_COURSES = "mod_quiz_get_quizzes_by_courses"
MOODLE_FUNC_GET_USER_QUIZ_ATTEMPTS = "mod_quiz_get_user_attempts"
MOODLE_FUNC_GET_POLICY_ACCEPTANCE_DATA =  \
    "local_raisecli_get_policy_acceptance_data"
MOODLE_REQUEST_TIMEOUT = 360  # 6 minutes


def convert_moodle_params(data, prefix=""):
    """Given a dict / array, convert into a flat dict that Moodle expects
    where the key names define the structure.
    """
    result = {}

    if not isinstance(data, (list, dict)):
        result[prefix] = data
        return result

    if not prefix:
        prefix = "{0}"
    else:
        prefix += "[{0}]"

    if isinstance(data, list):
        for idx, val in enumerate(data):
            elem_data = convert_moodle_params(
                val,
                prefix.format(idx)
            )
            result.update(elem_data)
    elif isinstance(data, dict):
        for key, val in data.items():
            elem_data = convert_moodle_params(
                val,
                prefix.format(key)
            )
            result.update(elem_data)

    return result


def check_for_moodle_error(result):
    """Check for errors before returning result"""
    result.raise_for_status()

    # Errors processing a request don't result in a non-success status code.
    # Instead Moodle will return a JSON object with exception details.
    result_json = result.json()
    try:
        if result_json.get('exception'):
            raise Exception(result_json)
    except AttributeError:
        pass

    return result_json


class MoodleClient:
    def __init__(self, session, moodle_url, moodle_token):
        self.session = session
        self.moodle_url = moodle_url
        self.service_endpoint = f"{moodle_url}{MOODLE_WEBSERVICE_PATH}"
        self.token = moodle_token

    def _create_params(self, service_function, data):
        params = {
            "wsfunction": service_function,
            "moodlewsrestformat": "json",
            "wstoken": self.token
        }
        if data:
            params.update(convert_moodle_params(data))
        return params

    def _post(self, service_function, data):
        """POST to service function with provided data as parameters"""
        res = self.session.post(
            self.service_endpoint,
            self._create_params(service_function, data),
            timeout=MOODLE_REQUEST_TIMEOUT
        )
        return check_for_moodle_error(res)

    def _get(self, service_function, data=None):
        """GET to service function with provided data as parameters"""
        res = self.session.get(
            self.service_endpoint,
            params=self._create_params(service_function, data),
            timeout=MOODLE_REQUEST_TIMEOUT
        )
        return check_for_moodle_error(res)

    def copy_course(
        self, source_id, course_name, course_shortname, course_category_id,
        include_users=False
    ):
        data = {
            "courseid": source_id,
            "fullname": course_name,
            "shortname": course_shortname,
            "categoryid": course_category_id,
            "options": [{"name": "users",
                        "value": ("1" if include_users else "0")}]
        }
        return self._post(
            MOODLE_FUNC_DUPLICATE_COURSE,
            data
        )

    def import_course(self, source_id, target_id):
        data = {
            "importfrom": source_id,
            "importto": target_id
        }

        return self._post(
            MOODLE_FUNC_IMPORT_COURSE,
            data
        )

    def get_courses(self):
        return self._get(MOODLE_FUNC_GET_COURSES)

    def get_course_by_shortname(self, shortname):
        data = {
            "field": "shortname",
            "value": shortname
        }
        return self._get(MOODLE_FUNC_GET_COURSES_BY_FIELD, data)

    def get_self_enrolment_methods(self, course_id, role_id):
        data = {
            "courseid": course_id,
            "roleid": role_id
        }
        return self._get(MOODLE_FUNC_GET_SELF_ENROLMENT_METHODS, data)

    def get_role_by_shortname(self, shortname):
        data = {
            "shortname": shortname
        }
        return self._get(MOODLE_FUNC_GET_ROLE_BY_SHORTNAME, data)

    def enable_self_enrolment_method(self, enrol_id):
        data = {
            "enrolid": enrol_id
        }
        return self._post(MOODLE_FUNC_ENABLE_SELF_ENROLMENT_METHOD, data)

    def set_self_enrolment_method_key(self, enrol_id, enrol_key):
        data = {
            "enrolid": enrol_id,
            "enrolkey": enrol_key
        }
        return self._post(MOODLE_FUNC_SET_SELF_ENROLMENT_METHOD_KEY, data)

    def get_user_by_email(self, email):
        data = {
            "criteria": [{
                "key": "email",
                "value": email
            }]
        }
        res = self._get(MOODLE_FUNC_GET_USERS, data)
        user_data = res["users"]

        if len(user_data) > 1:
            raise Exception(f"Multiple users returned with email {email}")

        if user_data:
            return user_data[0]
        else:
            return None

    def create_user(self, firstname, lastname, email, auth):
        # Moodle requires lower case in usernames and for consistency we'll
        # go ahead and use the same value for email
        lowercase_email = email.lower()
        user_data = {
            "username": lowercase_email,
            "firstname": firstname,
            "lastname": lastname,
            "email": lowercase_email,
            "auth": auth
        }
        # We set a password value if auth is manual so Moodle doesn't generate
        # and email one to the user.
        if auth == "manual":
            user_data["password"] = utils.generate_password()
        data = {
            "users": [user_data]
        }
        res = self._post(MOODLE_FUNC_CREATE_USERS, data)
        return res[0]

    def enrol_user(self, course_id, user_id, role_id):
        data = {
            "enrolments": [{
                "courseid": course_id,
                "userid": user_id,
                "roleid": role_id
            }]
        }
        return self._post(MOODLE_FUNC_ENROL_USER, data)

    def unenrol_user(self, course_id, user_id):
        data = {
            "enrolments": [{
                "courseid": course_id,
                "userid": user_id,
            }]
        }
        return self._post(MOODLE_FUNC_UNENROL_USER, data)

    def get_grades_by_course(self, course_id):
        data = {
            'courseid': course_id
        }
        return self._get(MOODLE_FUNC_GRADEREPORT_USER_GET_GRADE_ITEMS, data)

    def get_users_by_course(self, course_id):
        data = {
            "courseid": course_id
        }
        return self._get(MOODLE_FUNC_CORE_ENROL_GET_ENROLLED_USERS, data)

    def get_course_enrolment_url(self, course_id):
        return f"{self.moodle_url}/enrol/index.php?id={course_id}"

    def get_user_uuids(self, user_ids=[]):
        ids_list = []
        for id in user_ids:
            ids_list.append({'id': id})
        params = {'user_ids': ids_list}
        return self._get(MOODLE_FUNC_GET_USER_UUIDS, params)

    def get_quizzes_by_courses(self, course_ids):
        data = {
            "courseids": course_ids
        }
        return self._get(MOODLE_FUNC_GET_QUIZZES_BY_COURSES, data)

    def get_user_quiz_attempts(self, user_id, quiz_id):
        data = {
            "userid": user_id,
            "quizid": quiz_id
        }
        return self._get(MOODLE_FUNC_GET_USER_QUIZ_ATTEMPTS, data)

    def get_quiz_attempt_details(self, attempt_id):
        data = {
            "attemptid": attempt_id
        }
        return self._get(MOODLE_FUNC_GET_QUIZ_ATTEMPT, data)

    def get_policy_acceptance_data(self, policyversionid):
        data = {
            "policyversionid": policyversionid,
        }
        return self._get(MOODLE_FUNC_GET_POLICY_ACCEPTANCE_DATA, data)
