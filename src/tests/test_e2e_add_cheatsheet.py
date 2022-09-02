import re

import requests

from app import app
from tests.test_e2e_base import TestE2eBase, URL


# pylint: disable=R0904 (too-many-public-methods)
class TestE2eAddCheatsheet(TestE2eBase):
    def test_add_cheatsheet(self):
        # add a cheatsheet
        response = self._add_cheatsheet("test_snippet", "test_section")
        self._compare_num_cheatsheets(response, 1)

        # add another cheatsheet
        response = self._add_cheatsheet("test_snippet_2", "test_section_2")
        self._compare_num_cheatsheets(response, 2)

        # validate fields order
        pattern = "test_snippet.*test_snippet_2"
        assert re.search(pattern, response.text)

    def test_add_cheatsheet_with_missing_section(self):
        """
        section is optional field - adding a cheatsheet should succeed.
        """
        response = self._add_cheatsheet("test_snippet", "")
        self._compare_num_cheatsheets(response, 1)

    def test_add_cheatsheet_internal_err(self):
        # delete the db in order to get an internal error.
        self._delete_db()

        response = self._add_cheatsheet("test_snippet", "test_section")
        self._compare_num_cheatsheets(response, 0, db_avail=False)
        assert response.text.count(app.ADD_CHEATSHEET_ERR_MSG) == 1
        assert response.text.count(app.GET_CHEATSHEETS_ERR_MSG) == 1

        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 0, db_avail=False)
        assert response.text.count(app.ADD_CHEATSHEET_ERR_MSG) == 0
        assert response.text.count(app.GET_CHEATSHEETS_ERR_MSG) == 1

    def test_add_cheatsheet_success_msg(self):
        # add a cheatsheet
        response = self._add_cheatsheet("test_snippet", "test_section")
        self._compare_num_cheatsheets(response, 1)
        assert response.text.count(app.ADD_CHEATSHEET_OK_MSG) == 1

        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 1)
        assert response.text.count(app.ADD_CHEATSHEET_OK_MSG) == 0

        # add another cheatsheet
        response = self._add_cheatsheet("test_snippet_2", "test_section_2")
        self._compare_num_cheatsheets(response, 2)
        assert response.text.count(app.ADD_CHEATSHEET_OK_MSG) == 1

        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 2)
        assert response.text.count(app.ADD_CHEATSHEET_OK_MSG) == 0

    def test_add_cheatsheet_snippet_required(self):
        response = self._add_cheatsheet("", "test_section")
        self._compare_num_cheatsheets(response, 0)
        assert response.text.count(app.ADD_CHEATSHEET_SNIPPET_REQUIRED_MSG) == 1

    def test_add_cheatsheet_no_fields(self):
        response = self._add_cheatsheet("", "")
        self._compare_num_cheatsheets(response, 0)
        assert response.text.count(app.ADD_CHEATSHEET_SNIPPET_REQUIRED_MSG) == 1

    def test_add_cheatsheet_snippet_whitespace(self):
        response = self._add_cheatsheet(" ", "")
        self._compare_num_cheatsheets(response, 0)
        assert response.text.count(app.ADD_CHEATSHEET_SNIPPET_REQUIRED_MSG) == 1

    def test_add_cheatsheet_snippet_tab(self):
        response = self._add_cheatsheet("\t", "")
        self._compare_num_cheatsheets(response, 0)
        assert response.text.count(app.ADD_CHEATSHEET_SNIPPET_REQUIRED_MSG) == 1

    def test_add_cheatsheet_snippet_newline(self):
        response = self._add_cheatsheet("\n", "")
        self._compare_num_cheatsheets(response, 0)
        assert response.text.count(app.ADD_CHEATSHEET_SNIPPET_REQUIRED_MSG) == 1

    def test_sql_escaping(self):
        # test single quote
        response = self._add_cheatsheet("'select *'", "'select *'")
        self._compare_num_cheatsheets(response, 1)
        assert response.text.count(app.ADD_CHEATSHEET_OK_MSG) == 1

        # test double quote
        response = self._add_cheatsheet('"select *"', '"select *"')
        self._compare_num_cheatsheets(response, 2)
        assert response.text.count(app.ADD_CHEATSHEET_OK_MSG) == 1

    def test_whitespace(self):
        response = self._add_cheatsheet("test snippet", "test section")
        self._compare_num_cheatsheets(response, 1)
        assert response.text.count(app.ADD_CHEATSHEET_OK_MSG) == 1
        assert "test snippet" in response.text \
            and "test section" in response.text

    def test_input_values_on_err(self):
        """
        If "add cheatsheet" operation fail,
        fields that were entered by user should still show up.
        """
        # error due to missing snippet
        response = self._add_cheatsheet("", "test_section")
        self._compare_num_cheatsheets(response, 0)
        assert response.text.count(app.ADD_CHEATSHEET_SNIPPET_REQUIRED_MSG) == 1
        assert 'value="test_section"' in response.text

        # internal error
        self._delete_db()
        response = self._add_cheatsheet("test_snippet", "test_section")
        self._compare_num_cheatsheets(response, 0, db_avail=False)
        assert response.text.count(app.ADD_CHEATSHEET_ERR_MSG) == 1
        assert response.text.count(app.GET_CHEATSHEETS_ERR_MSG) == 1
        assert 'value="test_snippet"' in response.text \
            and 'value="test_section"' in response.text

    def test_escaped_input_values_on_err(self):
        """
        If "add cheatsheet" operation fail,
        fields that were entered by user should still show up.

        test that the values are escaped.
        """
        self._delete_db()
        response = self._add_cheatsheet("<test_snippet>", "<test_section>")
        self._compare_num_cheatsheets(response, 0, db_avail=False)
        assert response.text.count(app.ADD_CHEATSHEET_ERR_MSG) == 1
        assert response.text.count(app.GET_CHEATSHEETS_ERR_MSG) == 1
        assert 'value="&lt;test_snippet&gt;"' in response.text \
            and 'value="&lt;test_section&gt;"' in response.text

    def test_no_input_values_on_success(self):
        """
        If "add cheatsheet" operation fail,
        fields that were entered by user should still show up.

        test that there are no values on success.
        """
        response = self._add_cheatsheet("<test_snippet>", "<test_section>")
        self._compare_num_cheatsheets(response, 1)
        assert response.text.count(app.ADD_CHEATSHEET_OK_MSG) == 1
        assert 'value="&lt;test_snippet&gt;"' not in response.text \
            and 'value="&lt;test_section&gt;"' not in response.text
