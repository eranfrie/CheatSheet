import re

import requests

from app import app
from tests.test_e2e_base import TestE2eBase, URL


# pylint: disable=R0904 (too-many-public-methods)
class TestE2eAddBookmark(TestE2eBase):
    def test_add_bookmark(self):
        # add a bookmark
        response = self._add_bookmark("test_snippet", "test_section")
        self._compare_num_bookmarks(response, 1)

        # add another bookmark
        response = self._add_bookmark("test_snippet_2", "test_section_2")
        self._compare_num_bookmarks(response, 2)

        # validate fields order
        pattern = "test_snippet.*test_snippet_2"
        assert re.search(pattern, response.text)

    def test_add_bookmark_with_missing_section(self):
        """
        section is optional field - adding a bookmark should succeed.
        """
        response = self._add_bookmark("test_snippet", "")
        self._compare_num_bookmarks(response, 1)

    def test_add_bookmark_internal_err(self):
        # delete the db in order to get an internal error.
        self._delete_db()

        response = self._add_bookmark("test_snippet", "test_section")
        self._compare_num_bookmarks(response, 0, db_avail=False)
        assert response.text.count(app.ADD_BOOKMARK_ERR_MSG) == 1
        assert response.text.count(app.GET_BOOKMARKS_ERR_MSG) == 1

        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 0, db_avail=False)
        assert response.text.count(app.ADD_BOOKMARK_ERR_MSG) == 0
        assert response.text.count(app.GET_BOOKMARKS_ERR_MSG) == 1

    def test_add_bookmark_success_msg(self):
        # add a bookmark
        response = self._add_bookmark("test_snippet", "test_section")
        self._compare_num_bookmarks(response, 1)
        assert response.text.count(app.ADD_BOOKMARK_OK_MSG) == 1

        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 1)
        assert response.text.count(app.ADD_BOOKMARK_OK_MSG) == 0

        # add another bookmark
        response = self._add_bookmark("test_snippet_2", "test_section_2")
        self._compare_num_bookmarks(response, 2)
        assert response.text.count(app.ADD_BOOKMARK_OK_MSG) == 1

        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 2)
        assert response.text.count(app.ADD_BOOKMARK_OK_MSG) == 0

    def test_add_bookmark_snippet_required(self):
        response = self._add_bookmark("", "test_section")
        self._compare_num_bookmarks(response, 0)
        assert response.text.count(app.ADD_BOOKMARK_SNIPPET_REQUIRED_MSG) == 1

    def test_add_bookmark_no_fields(self):
        response = self._add_bookmark("", "")
        self._compare_num_bookmarks(response, 0)
        assert response.text.count(app.ADD_BOOKMARK_SNIPPET_REQUIRED_MSG) == 1

    def test_add_bookmark_snippet_whitespace(self):
        response = self._add_bookmark(" ", "")
        self._compare_num_bookmarks(response, 0)
        assert response.text.count(app.ADD_BOOKMARK_SNIPPET_REQUIRED_MSG) == 1

    def test_add_bookmark_snippet_tab(self):
        response = self._add_bookmark("\t", "")
        self._compare_num_bookmarks(response, 0)
        assert response.text.count(app.ADD_BOOKMARK_SNIPPET_REQUIRED_MSG) == 1

    def test_add_bookmark_snippet_newline(self):
        response = self._add_bookmark("\n", "")
        self._compare_num_bookmarks(response, 0)
        assert response.text.count(app.ADD_BOOKMARK_SNIPPET_REQUIRED_MSG) == 1

    def test_sql_escaping(self):
        # test single quote
        response = self._add_bookmark("'select *'", "'select *'")
        self._compare_num_bookmarks(response, 1)
        assert response.text.count(app.ADD_BOOKMARK_OK_MSG) == 1

        # test double quote
        response = self._add_bookmark('"select *"', '"select *"')
        self._compare_num_bookmarks(response, 2)
        assert response.text.count(app.ADD_BOOKMARK_OK_MSG) == 1

    def test_whitespace(self):
        response = self._add_bookmark("test snippet", "test section")
        self._compare_num_bookmarks(response, 1)
        assert response.text.count(app.ADD_BOOKMARK_OK_MSG) == 1
        assert "test snippet" in response.text \
            and "test section" in response.text

    def test_input_values_on_err(self):
        """
        If "add bookmark" operation fail,
        fields that were entered by user should still show up.
        """
        # error due to missing snippet
        response = self._add_bookmark("", "test_section")
        self._compare_num_bookmarks(response, 0)
        assert response.text.count(app.ADD_BOOKMARK_SNIPPET_REQUIRED_MSG) == 1
        assert 'value="test_section"' in response.text

        # internal error
        self._delete_db()
        response = self._add_bookmark("test_snippet", "test_section")
        self._compare_num_bookmarks(response, 0, db_avail=False)
        assert response.text.count(app.ADD_BOOKMARK_ERR_MSG) == 1
        assert response.text.count(app.GET_BOOKMARKS_ERR_MSG) == 1
        assert 'value="test_snippet"' in response.text \
            and 'value="test_section"' in response.text

    def test_escaped_input_values_on_err(self):
        """
        If "add bookmark" operation fail,
        fields that were entered by user should still show up.

        test that the values are escaped.
        """
        self._delete_db()
        response = self._add_bookmark("<test_snippet>", "<test_section>")
        self._compare_num_bookmarks(response, 0, db_avail=False)
        assert response.text.count(app.ADD_BOOKMARK_ERR_MSG) == 1
        assert response.text.count(app.GET_BOOKMARKS_ERR_MSG) == 1
        assert 'value="&lt;test_snippet&gt;"' in response.text \
            and 'value="&lt;test_section&gt;"' in response.text

    def test_no_input_values_on_success(self):
        """
        If "add bookmark" operation fail,
        fields that were entered by user should still show up.

        test that there are no values on success.
        """
        response = self._add_bookmark("<test_snippet>", "<test_section>")
        self._compare_num_bookmarks(response, 1)
        assert response.text.count(app.ADD_BOOKMARK_OK_MSG) == 1
        assert 'value="&lt;test_snippet&gt;"' not in response.text \
            and 'value="&lt;test_section&gt;"' not in response.text
