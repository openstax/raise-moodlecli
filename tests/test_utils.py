from moodlecli.moodle import MoodleClient, MOODLE_WEBSERVICE_PATH
from moodlecli import utils
import pytest
import requests

TEST_MOODLE_URL = "http://test-things"
TEST_MOODLE_TOKEN = "e4586db9345084f15abc7326b84dde21"
TEST_ENV = {'MOODLE_URL': TEST_MOODLE_URL, 'MOODLE_TOKEN': TEST_MOODLE_TOKEN}
CONTEXT_MOODLE_CLIENT_KEY = "MOODLE_CLIENT"


def test_maybe_user_uuids(requests_mock):
    moodle = MoodleClient(
        requests.Session(),
        TEST_MOODLE_URL,
        TEST_MOODLE_TOKEN
    )

    requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}',
                      json={'exception': 'value'})

    with pytest.raises(Exception):
        utils.maybe_user_uuids(moodle)

    requests_mock.get(f'{TEST_MOODLE_URL}{MOODLE_WEBSERVICE_PATH}',
                      json={'exception': 'dml_missing_record_exception'})

    assert (utils.maybe_user_uuids(moodle) == [])
