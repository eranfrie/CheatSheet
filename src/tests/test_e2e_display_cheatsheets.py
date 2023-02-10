import requests

from app import app
from tests.test_e2e_base import TestE2eBase, URL


class TestE2eDisplayCheatsheets(TestE2eBase):
    def test_empty_get(self):
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 0)
        # test that where there are 0 cheatsheets,
        # we don't accidentally display the error msg
        assert app.GET_CHEATSHEETS_ERR_MSG not in response.text

    def test_get_one_cheatsheet(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 1)

    def test_get_two_cheatsheet(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        self._add_cheatsheet_to_db("test_snippet_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 2)

    def test_get_internal_err(self):
        # delete the db in order to get an internal error.
        self._delete_db()

        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 0, db_avail=False)
        assert response.text.count(app.GET_CHEATSHEETS_ERR_MSG) == 1

    def test_markdown_inline_code(self):
        """Test that an inline code is properly highlighted."""
        self._add_cheatsheet_to_db("test_`snippet`_1", "test_section_1")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 1)
        assert "background-color:LightGray;" in response.text
