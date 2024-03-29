import os
import json
import csv
import click
import requests
from .moodle import MoodleClient
from . import utils
from . import aws

CONTEXT_MOODLE_CLIENT_KEY = "MOODLE_CLIENT"


@click.pass_context
def get_moodle_client(ctx):
    return ctx.obj[CONTEXT_MOODLE_CLIENT_KEY]


@click.group()
@click.pass_context
def cli(ctx):
    moodle_url = os.getenv("MOODLE_URL")
    moodle_token = os.getenv("MOODLE_TOKEN")
    if not moodle_url or not moodle_token:
        click.echo(
            "Please set MOODLE_URL and MOODLE_TOKEN in your environment "
            "before running the CLI"
        )
        ctx.exit(1)

    moodle = MoodleClient(
        requests.Session(),
        moodle_url,
        moodle_token
    )

    ctx.obj = {
        CONTEXT_MOODLE_CLIENT_KEY: moodle
    }


@cli.command()
@click.argument("source_id")
@click.argument("course_name")
@click.argument("course_shortname")
@click.argument("course_category_id")
@click.option('-u', '--include-users', is_flag=True,
              help="Copy enrolled users from base class")
def copy_course(
                source_id, course_name, course_shortname, course_category_id,
                include_users
):
    """Copy course with SOURCE_ID to new course"""
    moodle = get_moodle_client()
    res = moodle.copy_course(
        source_id,
        course_name,
        course_shortname,
        course_category_id,
        include_users
    )
    click.echo(json.dumps(res, indent=4))


@cli.command()
@click.argument("source_id")
@click.argument("target_id")
def import_course(source_id, target_id):
    """Import content from course SOURCE_ID to course TARGET_ID"""

    moodle = get_moodle_client()
    res = moodle.import_course(source_id, target_id)
    click.echo(json.dumps(res, indent=4))


@cli.command()
def courses():
    """Get list of courses"""
    moodle = get_moodle_client()
    res = moodle.get_courses()
    table = utils.stylize_courses(res)
    click.echo(table)


@cli.command()
@click.argument("course_id")
@click.argument("role_id")
def self_enrolment_methods(course_id, role_id):
    """Get self enrolment methods by course and role"""
    moodle = get_moodle_client()
    res = moodle.get_self_enrolment_methods(course_id, role_id)
    click.echo(json.dumps(res, indent=4))


@cli.command()
@click.argument("shortname")
def role_info(shortname):
    """Get role data by shortname"""
    moodle = get_moodle_client()
    res = moodle.get_role_by_shortname(shortname)
    click.echo(json.dumps(res, indent=4))


@cli.command()
@click.argument("enrol_id")
def enable_self_enrolment_method(enrol_id):
    """Enable self enrolment method"""
    moodle = get_moodle_client()
    res = moodle.enable_self_enrolment_method(enrol_id)
    click.echo(json.dumps(res, indent=4))


@cli.command()
@click.argument("enrol_id")
@click.argument("enrol_key")
def set_self_enrolment_method_key(enrol_id, enrol_key):
    """Set self enrolment method key"""
    moodle = get_moodle_client()
    res = moodle.set_self_enrolment_method_key(enrol_id, enrol_key)
    click.echo(json.dumps(res, indent=4))


@cli.command()
@click.argument('output_csv', type=click.File(mode='w'))
def course_bulk_csv(output_csv):
    """Output an empty CSV template for course-bulk-setup"""
    writer = csv.DictWriter(
        output_csv,
        utils.course_bulk_input_csv_fieldnames()
    )
    writer.writeheader()


@cli.command()
@click.argument('base_course_id')
@click.argument('coursedata_csv', type=click.File(mode='r'))
@click.argument('courseoutput_csv', type=click.File(mode='w'))
def course_bulk_setup(base_course_id, coursedata_csv, courseoutput_csv):
    """Bulk setup of courses using an existing base course"""
    moodle = get_moodle_client()

    # Query required role data from instance
    # Note: The "teacher" shortname is the non-editing teacher role
    teacher_role = moodle.get_role_by_shortname("teacher")
    student_role = moodle.get_role_by_shortname("student")

    updated_courses = []

    course_reader = csv.DictReader(coursedata_csv)
    try:
        for course in course_reader:
            updated_course = utils.setup_duplicate_course(
                moodle,
                base_course_id,
                course,
                teacher_role["id"],
                student_role["id"]
            )
            updated_courses.append(updated_course)
    finally:
        writer = csv.DictWriter(
            courseoutput_csv,
            utils.course_bulk_output_csv_fieldnames()
        )
        writer.writeheader()
        writer.writerows(updated_courses)


@cli.command()
@click.argument('output_csv', type=click.File(mode='w'))
def enrol_bulk_csv(output_csv):
    """Output an empty CSV template for enrol-bulk"""
    writer = csv.DictWriter(
        output_csv,
        utils.enrol_bulk_input_csv_fieldnames()
    )
    writer.writeheader()


@cli.command()
@click.argument('course_id')
@click.argument('role_shortname')
@click.argument('userdata_csv', type=click.File(mode='r'))
def enrol_bulk(course_id, role_shortname, userdata_csv):
    """Bulk enrol users to course with role"""
    moodle = get_moodle_client()

    role = moodle.get_role_by_shortname(role_shortname)

    user_reader = csv.DictReader(userdata_csv)
    for user in user_reader:
        user_id = utils.create_or_get_user(
            moodle,
            user[utils.CSV_USER_FNAME],
            user[utils.CSV_USER_LNAME],
            user[utils.CSV_USER_EMAIL],
            user[utils.CSV_USER_AUTH]
        )
        moodle.enrol_user(course_id, user_id, role["id"])


@cli.command()
@click.argument('output_csv', type=click.File(mode='w'))
def unenrol_bulk_csv(output_csv):
    """Output an empty CSV template for unenrol-bulk"""
    writer = csv.DictWriter(
        output_csv,
        utils.unenrol_bulk_input_csv_fieldnames()
    )
    writer.writeheader()


@cli.command()
@click.argument('course_id')
@click.argument('userdata_csv', type=click.File(mode='r'))
def unenrol_bulk(course_id, userdata_csv):
    """Bulk unenrol users from course"""
    moodle = get_moodle_client()

    user_reader = csv.DictReader(userdata_csv)
    for user in user_reader:
        existing_user = moodle.get_user_by_email(
          user['user_email']
        )
        if existing_user:
            user_id = existing_user['id']
            moodle.unenrol_user(course_id, user_id)


@cli.command()
@click.argument('output_csv', type=click.File(mode='w'))
def import_bulk_csv(output_csv):
    """Output an empty CSV template for import-bulk"""
    writer = csv.DictWriter(
        output_csv,
        utils.import_bulk_input_csv_fieldnames()
    )
    writer.writeheader()


@cli.command()
@click.argument('source_course_id')
@click.argument('targetcourses_csv', type=click.File(mode='r'))
def import_bulk(source_course_id, targetcourses_csv):
    """Bulk operation to import content into multiple courses"""
    moodle = get_moodle_client()

    target_course_reader = csv.DictReader(targetcourses_csv)
    for target_course in target_course_reader:
        moodle.import_course(
            source_course_id,
            target_course[utils.CSV_COURSE_ID]
        )


@cli.command()
@click.argument('source_course_id')
@click.argument('bucket_name')
@click.argument('key')
def export_grades(source_course_id, bucket_name, key):
    """Output to JSON the grades for a given course into a s3 bucket"""
    moodle = get_moodle_client()

    old_grades = aws.get_json_data(bucket_name, key, {})
    new_grades = utils.update_grades_data(
        moodle,
        source_course_id,
        old_grades
    )
    aws.put_json_data(new_grades, bucket_name, key)


@cli.command()
@click.argument('source_course_id')
@click.argument('bucket_name')
@click.argument('key')
def export_users(source_course_id, bucket_name, key):
    """Collects user data and unique ids from moodle, injects
    the uuids into the user data, then outputs the user data to s3"""
    moodle = get_moodle_client()

    user_data = moodle.get_users_by_course(
        source_course_id
    )
    uuid_data = utils.maybe_user_uuids(moodle)
    user_data = utils.inject_uuids(uuid_data, user_data)

    aws.put_json_data(user_data, bucket_name, key)


@cli.command()
@click.argument('input_csv', type=click.File(mode='r'))
@click.argument('bucket_name')
@click.argument('directory')
@click.argument('data_type',
                type=click.Choice(['grades', 'users'], case_sensitive=False))
def export_bulk(input_csv, bucket_name, directory, data_type):
    """Outputs either grade data or user data (with unique ids) to a
    specified s3 bucket"""

    moodle = get_moodle_client()
    course_ids = csv.DictReader(input_csv)
    if data_type == 'users':
        uuid_data = utils.maybe_user_uuids(moodle)
    for row in course_ids:
        id = row[utils.CSV_COURSE_ID]
        key = f'{directory}/{id}.json'
        if data_type == 'grades':
            old_grades = aws.get_json_data(bucket_name, key, {})
            new_grades = utils.update_grades_data(
                moodle,
                id,
                old_grades
            )
            aws.put_json_data(new_grades, bucket_name, key)
        elif data_type == 'users':
            user_data = moodle.get_users_by_course(id)
            user_data = utils.inject_uuids(uuid_data, user_data)
            aws.put_json_data(user_data, bucket_name, key)


@cli.command()
@click.argument('output_csv', type=click.File(mode='w'))
def export_bulk_csv(output_csv):
    """Output an empty CSV template for course-bulk-setup"""
    writer = csv.DictWriter(
        output_csv,
        utils.bulk_export_csv_course_ids()
    )
    writer.writeheader()


@cli.command()
@click.argument('policyversionid')
@click.argument('bucket_name')
@click.argument('key')
def export_policy_acceptances(policyversionid, bucket_name, key):
    """Get policy acceptance data and save to JSON in S3"""
    moodle = get_moodle_client()

    policy_acceptance_data = moodle.get_policy_acceptance_data(
        policyversionid=policyversionid)
    aws.put_json_data(policy_acceptance_data, bucket_name, key)
