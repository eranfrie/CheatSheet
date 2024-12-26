import requests

from tests.test_e2e_base import TestE2eBase, URL
from app import app


class TestE2eEdit(TestE2eBase):
    # pylint: disable=R0201 (no-self-use)
    def _edit_cheatsheet(self, snippet_id, snippet, section):
        payload = {
            "snippet_id": snippet_id,
            "snippet": snippet,
            "section": section,
        }
        response = requests.post(URL.EDIT_SNIPPET.value, data=payload)
        return response

    def test_edit_success(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        response = self._edit_cheatsheet(1, "test_snippet_2", "test_section_2")
        self._compare_num_cheatsheets(response, 1)
        assert "test_snippet_2" in response.text and "test_section_2" in response.text
        assert app.EDIT_CHEATSHEET_OK_MSG in response.text
        assert "Add a snippet" in response.text

    def test_edit_fail_snippet_required(self):
        """Edit fails because snippet is a required field."""
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        response = self._edit_cheatsheet(1, "", "test_section_2")
        assert "test_snippet_1" not in response.text
        assert "test_section_2" in response.text
        assert app.SNIPPET_REQUIRED_MSG in response.text
        # stay in edit form
        assert "Edit a snippet" in response.text

    def test_edit_fail_db_not_accessible(self):
        self._delete_db()
        response = self._edit_cheatsheet(1, "test_snippet_2", "test_section_2")
        assert "test_snippet_2" in response.text and "test_section_2" in response.text
        assert app.EDIT_CHEATSHEET_ERR_MSG in response.text
        # stay in edit form
        assert "Edit a snippet" in response.text
