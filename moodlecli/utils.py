import string
import random
from prettytable import PrettyTable
from requests.exceptions import ConnectionError, Timeout
from time import sleep

CSV_INST_FNAME = 'instructor_firstname'
CSV_INST_LNAME = 'instructor_lastname'
CSV_INST_EMAIL = 'instructor_email'
CSV_INST_AUTH = 'instructor_auth_type'
CSV_USER_FNAME = 'user_firstname'
CSV_USER_LNAME = 'user_lastname'
CSV_USER_EMAIL = 'user_email'
CSV_USER_AUTH = 'user_auth_type'
CSV_COURSE_NAME = 'course_name'
CSV_COURSE_SHORTNAME = 'course_shortname'
CSV_COURSE_CATEGORY = 'course_category'
CSV_COURSE_ID = "course_id"
CSV_COURSE_ENROLMENT_URL = "course_enrolment_url"
CSV_COURSE_ENROLMENT_KEY = "course_enrolment_key"


def generate_password(length=12):
    """Create a password value"""
    # We incorporate at least 1 digit, 1 upper case, 1 lower case, and
    # 1 non-alphanumeric

    non_alphanum = ".,;:!?_-+/*@#&$"

    password = []
    password.append(random.choice(string.digits))
    password.append(random.choice(string.ascii_uppercase))
    password.append(random.choice(string.ascii_lowercase))
    password.append(random.choice(non_alphanum))

    all_characters = string.digits + string.ascii_uppercase + \
        string.ascii_lowercase + non_alphanum
    password += random.choices(
        all_characters,
        k=max(0, length - len(password))
    )

    random.shuffle(password)
    return ''.join(password)


def generate_friendly_password():
    adjectives = ["cold", "silly", "suave", "pensive", "lying", "pious",
                  "sweaty", "bald", "lovely", "affirming"]
    animals = ["panda", "cow", "penguin", "flamingo", "worm", "crab",
               "shark", "hippo", "locust", "spider"]

    password = []
    password.append(random.choice(adjectives))
    password.append("-")
    password.append(random.choice(animals))
    password.append("-")
    password.append(f'{random.randrange(0, 10**4):04}')

    return ''.join(password)


def course_bulk_input_csv_fieldnames():
    """Return array of fieldnames used / expected in input CSV for course
    bulk setup"""
    return [
        CSV_INST_FNAME,
        CSV_INST_LNAME,
        CSV_INST_EMAIL,
        CSV_INST_AUTH,
        CSV_COURSE_NAME,
        CSV_COURSE_SHORTNAME,
        CSV_COURSE_CATEGORY
    ]


def course_bulk_output_csv_fieldnames():
    """Return array of fieldnames in output CSV for course bulk setup"""
    return course_bulk_input_csv_fieldnames() + [
        CSV_COURSE_ID,
        CSV_COURSE_ENROLMENT_URL,
        CSV_COURSE_ENROLMENT_KEY
    ]


def enrol_bulk_input_csv_fieldnames():
    """Return array of fieldnames used in input CSV for enrol"""
    return [
        CSV_USER_FNAME,
        CSV_USER_LNAME,
        CSV_USER_EMAIL,
        CSV_USER_AUTH
    ]


def unenrol_bulk_input_csv_fieldnames():
    """Return array of email addresses used in input CSV for unenrol"""
    return [
        CSV_USER_EMAIL
    ]


def import_bulk_input_csv_fieldnames():
    """Return array of fieldnames used in inpu CSV for bulk import"""
    return [
        CSV_COURSE_ID
    ]


def bulk_export_csv_course_ids():
    """Return array of fieldnames used in output CSV for bulk export"""
    return {
        CSV_COURSE_ID
    }


def create_or_get_user(moodle_client, firstname, lastname, email, auth):
    """Create a user account if it doesn't exist and return user ID"""
    existing_user = moodle_client.get_user_by_email(
        email
    )
    if existing_user:
        user_id = existing_user['id']
    else:
        new_user = moodle_client.create_user(
            firstname,
            lastname,
            email,
            auth
        )
        user_id = new_user["id"]
    return user_id


def stylize_courses(courses_json):
    t = PrettyTable()
    fields = ['fullname', 'id', 'visible', 'categoryid']
    t.field_names = fields
    for course in courses_json:
        row = []
        for col in fields:
            row.append(course[col])
        t.add_row(row)

    t.align["fullname"] = "l"
    return t.get_string(sortby='id')


def setup_duplicate_course(
    moodle_client, base_course_id, coursedata, instructor_role_id,
    student_role_id
):
    """Setup a new course using a base and data from bulk CSV"""
    # Retrieve or create teacher account
    instructor_user_id = create_or_get_user(
        moodle_client,
        coursedata[CSV_INST_FNAME],
        coursedata[CSV_INST_LNAME],
        coursedata[CSV_INST_EMAIL],
        coursedata[CSV_INST_AUTH]
    )
    try:
        # Create a duplicate course using the base course
        new_course = moodle_client.copy_course(
            base_course_id,
            coursedata[CSV_COURSE_NAME],
            coursedata[CSV_COURSE_SHORTNAME],
            coursedata[CSV_COURSE_CATEGORY]
        )
        new_course_id = new_course["id"]
    except (ConnectionError, Timeout):
        # Implement work around for Global Accelerator timeout of 340s
        # (refer to https://github.com/openstax/k12/issues/316 for details)
        print("Remote disconnected during course copy!")
        print(f"Polling for course {coursedata[CSV_COURSE_SHORTNAME]}...")
        course_found = False
        while not course_found:
            sleep(30)
            print("Querying current courses")
            courses = moodle_client.get_courses()
            for course in courses:
                if course["shortname"] == coursedata[CSV_COURSE_SHORTNAME]:
                    new_course_id = course["id"]
                    print(f"Found copy: Course ID {new_course_id}")
                    course_found = True
                    break

    # Enrol teacher user as a course instructor
    moodle_client.enrol_user(
        new_course_id,
        instructor_user_id,
        instructor_role_id
    )

    # Get enrolment ID for course and student role
    enrolments = moodle_client.get_self_enrolment_methods(
        new_course_id,
        student_role_id
    )
    if len(enrolments) != 1:
        raise Exception(
            "Unexpected number of student self enrolment methods found "
            f"for course {new_course_id}"
        )
    student_enrolment_id = enrolments[0]["id"]

    # Enable enrolment and set enrolment key
    moodle_client.enable_self_enrolment_method(student_enrolment_id)
    enrolment_key = generate_friendly_password()
    moodle_client.set_self_enrolment_method_key(
        student_enrolment_id,
        enrolment_key
    )

    # Return updated course dict adding course ID and enrolment URL / key
    coursedata[CSV_COURSE_ID] = new_course_id
    coursedata[CSV_COURSE_ENROLMENT_URL] = \
        moodle_client.get_course_enrolment_url(new_course_id)
    coursedata[CSV_COURSE_ENROLMENT_KEY] = enrolment_key

    return coursedata


def inject_uuids(uuid_data, user_data):
    uuid_map = {}
    # Make a hash of all user_ids to uuids
    for item in uuid_data:
        uuid_map[int(item['user_id'])] = item['user_uuid']

    # Add uuids to user data
    for user in user_data:
        user_id = int(user['id'])
        if user_id in uuid_map.keys():
            user['uuid'] = uuid_map[user_id]
        else:
            user['uuid'] = None
    return user_data


def maybe_user_uuids(moodle_client, user_ids=[]):
    try:
        return moodle_client.get_user_uuids(user_ids)
    except Exception as e:
        if e.args[0]['exception'] == 'dml_missing_record_exception':
            return []
        else:
            raise e


def update_grades_data(moodle_client, course_id, old_grades):
    """This utility function builds a single object which includes data from
    multiple Moodle endpoints. The final object includes the following:
    {
        "usergrades": [ // Data as returned by get_grades_by_course ],
        "quizzes": [ // Data as returned by get_quizzes_by_courses ],
        "attempts": {
            "{user_id}": {
                "{quiz_id}": {
                    "summaries": [
                        // Data as returned by get_user_quiz_attempts
                    ]
                    "details": {
                        "{attempt_id}": {
                            // Data as returned by get_quiz_attempt_details
                        }
                    }
                }
            }
        }
    }

    The function expects the same structure when parsing to determine if
    data from old_grades can be used as a cache to avoid unnecessary calls
    to Moodle.
    """

    def _attempts_data_is_stale(attempts, user_id, quiz_id, new_attempt_ts):
        old_user_attempts = attempts.get(user_id, {})
        old_quiz_attempts = old_user_attempts.get(quiz_id, {})

        # Use the gradednotificationsenttime to decide whether data is stale
        latest_found_ts = 0
        for summary in old_quiz_attempts.get("summaries", []):
            tmp_attempt_ts = summary["gradednotificationsenttime"]
            if (tmp_attempt_ts is not None) and \
               (latest_found_ts < tmp_attempt_ts):
                latest_found_ts = tmp_attempt_ts

        return new_attempt_ts > latest_found_ts

    # Always pull latest grades and quiz data. The grades data is the basis
    # of the data object returned by this function.
    new_grades = moodle_client.get_grades_by_course(course_id)
    new_quizzes = moodle_client.get_quizzes_by_courses([course_id])

    new_grades["quizzes"] = new_quizzes["quizzes"]
    new_grades["attempts"] = {}

    new_usergrades = new_grades["usergrades"]
    old_attempts = old_grades.get("attempts", {})

    for new_usergrade in new_usergrades:
        user_id = str(new_usergrade["userid"])
        new_grades["attempts"][user_id] = {}

        for new_gradeitem in new_usergrade["gradeitems"]:
            gradedatesubmitted = new_gradeitem["gradedatesubmitted"]
            if gradedatesubmitted is None:
                # Nothing more to do for this user + quiz combo
                continue
            quiz_id = str(new_gradeitem["iteminstance"])
            new_grades["attempts"][user_id][quiz_id] = {}
            tmp_attempts = {}
            if _attempts_data_is_stale(
                old_attempts,
                user_id,
                quiz_id,
                gradedatesubmitted
            ):
                # Fetch latest attempt summaries
                data = moodle_client.get_user_quiz_attempts(user_id, quiz_id)
                tmp_attempts["summaries"] = data["attempts"]
            else:
                # Copy data from old dataset
                tmp_attempts["summaries"] = \
                    old_attempts[user_id][quiz_id]["summaries"]

            tmp_attempts["details"] = {}
            for summary in tmp_attempts["summaries"]:
                attempt_id = str(summary["id"])
                maybe_attempt_details = old_attempts.get(user_id, {}).get(
                    quiz_id,
                    {}
                ).get("details", {}).get(attempt_id)

                if maybe_attempt_details:
                    attempt_details = maybe_attempt_details
                else:
                    attempt_details = \
                        moodle_client.get_quiz_attempt_details(attempt_id)
                tmp_attempts["details"][attempt_id] = attempt_details

            new_grades["attempts"][user_id][quiz_id] = tmp_attempts

    return new_grades
