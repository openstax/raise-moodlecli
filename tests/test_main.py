from urllib import request
import pytest
from moodlecli import main
import requests
import requests_mock as rm
import os


from click.testing import CliRunner
from moodlecli.main import cli

TEST_MOODLE_URL = "http://dagobah"
TEST_MOODLE_TOKEN = "1234"

# TEST_MOODLE_URL = "http://localhost8000"
# TEST_MOODLE_TOKEN = "478e0443d5075ad8fbcf1f2eac1ca787"

MOODLE_WEBSERVICE_PATH = "/webservice/rest/server.php"

def test_courses(requests_mock):
    runner = CliRunner()
    requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json={"foo": "bar"})
    result = runner.invoke(cli, ['courses'], env={'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN})
    assert result.exit_code == 0
    print(result.output)

def test_course_bulk_setup(requests_mock):
    runner = CliRunner()
    requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}', json = {"foo": "bar"})
    
    temp_path = "/tmp"

    #how do I know that the next level will open here? 
    # runner.isolated_filesystem(temp_dir=temp_path) 

    #if I don't use the file system does this work correctly? 
    f = open('test2.csv', 'w')
    f.write('instructor_firstname,instructor_lastname,instructor_email,instructor_auth_type,course_name,course_shortname,course_category\nTom,Michaels,tmichaels@gmail.com,manual,Algebra 1,A1,1')


    result = runner.invoke(cli, ['course_bulk_setup 2 test.csv output.csv'], env={'MOODLE_URL' : TEST_MOODLE_URL, "MOODLE_TOKEN" : TEST_MOODLE_TOKEN})
    
    assert result.exit_code == 0
    assert os.stat("output.csv").st_size != 0

# When I run this with pytest... what happens? how is it called? 
# It looks like all it does is run all of the functions that are within 'test_' files 
# So when I use pytest - how can I get printouts of what's happening - printouts happen in the console 
# in the middle of the dots 
# However, it's not clear that the new file I created showed up after running pytest
# When I sent in requests mock to the test - where does this come from? 
#   my guess is that pytest looks through those specific files in setup.cfg and then sends them in if need be. 
#   which makes running this file on it's own useless unless I want to import requests-mock at the top. I'm 
#   sure its a good thing because it makes everything much more modular - I would love to just be reassured. 

# test_course_bulk_setup(rm.Mocker())

# so its still not clear to me whats happening 


