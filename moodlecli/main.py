import os
import json
import csv
import click
import requests
from .moodle import MoodleClient
from . import utils


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
def copy_course(
    source_id, course_name, course_shortname, course_category_id
):
    """Copy course with SOURCE_ID to new course"""
    moodle = get_moodle_client()
    res = moodle.copy_course(
        source_id,
        course_name,
        course_shortname,
        course_category_id
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
    click.echo(json.dumps(res, indent=4))


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
            updated_course = utils.setup_duplicate_course(  #try catch, where after this fails you just move on 
                moodle,
                base_course_id,
                course,
                teacher_role["id"],
                student_role["id"]
            )
            updated_courses.append(updated_course)
    except: 
        print("ERROR: invalid entry in %s", coursedata_csv)

    # print("UPDATED COURSES: ", updated_courses)

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
