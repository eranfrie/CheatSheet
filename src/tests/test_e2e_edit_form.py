import requests

from tests.test_e2e_base import TestE2eBase, URL


class TestE2eEditForm(TestE2eBase):
    def test_edit_form(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        response = requests.get(URL.EDIT_FORM.value + "?id=1")
        assert response.status_code == 200
        assert "test_snippet_1" in response.text and "test_section_1" in response.text

        assert "Edit a snippet" in response.text
        assert "Preview" in response.text

    # pylint: disable=R0201 (no-self-use)
    def test_edit_form_invalid_snippet_id(self):
        """In case of invalid snippet id, main page is presented."""
        response = requests.get(URL.EDIT_FORM.value + "?id=1234")
        assert response.status_code == 200
        assert "Add a snippet" in response.text

    # pylint: disable=R0201 (no-self-use)
    def test_edit_form_snippet_id_missing_in_url(self):
        """In case of missing snippet id, main page is presented."""
        response = requests.get(URL.EDIT_FORM.value)
        assert response.status_code == 200
        assert "Add a snippet" in response.text

    def test_edit_form_db_not_accessible(self):
        """In case of no DB, main page is presented."""
        self._delete_db()
        response = requests.get(URL.EDIT_FORM.value + "?id=1")
        assert response.status_code == 200
        assert "Add a snippet" in response.text
