import base64

import requests

from app import app
from tests.test_e2e_base import TestE2eBase, URL


# disable similar code check
# pylint: disable=R0801
class TestE2eCheatsheetsEndpoint(TestE2eBase):
    def _compare_num_cheatsheets(self, response, expected_num_cheatsheets, db_avail=True):
        assert response.status_code == 200
        if db_avail:
            assert f"Total: {expected_num_cheatsheets}" in response.text
            assert self._count_cheatsheets_in_db() == expected_num_cheatsheets

    def test_empty(self):
        response = requests.get(URL.CHEATSHEETS.value)
        self._compare_num_cheatsheets(response, 0)
        # test that where there are 0 cheatsheets,
        # we don't accidentally display the error msg
        assert app.GET_CHEATSHEETS_ERR_MSG not in response.text

    def test_get_one_cheatsheet(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        response = requests.get(URL.CHEATSHEETS.value)
        self._compare_num_cheatsheets(response, 1)

    def test_get_two_cheatsheet(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        self._add_cheatsheet_to_db("test_snippet_2", "test_section_2")
        response = requests.get(URL.CHEATSHEETS.value)
        self._compare_num_cheatsheets(response, 2)

    def test_get_internal_err(self):
        # delete the db in order to get an internal error.
        self._delete_db()

        response = requests.get(URL.CHEATSHEETS.value)
        self._compare_num_cheatsheets(response, 0, db_avail=False)
        assert response.text.count(app.GET_CHEATSHEETS_ERR_MSG) == 1

    def test_search_no_results(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        self._add_cheatsheet_to_db("test_snippet_2", "test_section_2")
        response = requests.get(URL.CHEATSHEETS.value)
        self._compare_num_cheatsheets(response, 2)

        pattern = "test_snippet_3"
        encoded_pattern = base64.b64encode(pattern.encode("ascii"))
        response = requests.get(URL.CHEATSHEETS.value, params={"pattern": encoded_pattern})
        self._compare_num_cheatsheets(response, 0, db_avail=False)
        assert response.text.count("mark>") == 0

    def test_search_one_results(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        self._add_cheatsheet_to_db("test_snippet_2", "test_section_2")
        response = requests.get(URL.CHEATSHEETS.value)
        self._compare_num_cheatsheets(response, 2)

        pattern = "test_snippet_1"
        encoded_pattern = base64.b64encode(pattern.encode("ascii"))
        response = requests.get(URL.CHEATSHEETS.value, params={"pattern": encoded_pattern})
        self._compare_num_cheatsheets(response, 1, db_avail=False)
