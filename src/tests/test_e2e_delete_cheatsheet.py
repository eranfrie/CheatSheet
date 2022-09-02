import requests

from app import app
from tests.test_e2e_base import TestE2eBase, URL


class TestE2eDeleteCheatsheet(TestE2eBase):
    def test_delete_cheatsheet_success(self):
        self._add_cheatsheet_to_db("test_snippet", "test_section")
        assert self._count_cheatsheets_in_db() == 1

        cheatsheet_id = 1
        payload = {"cheatsheet_id": cheatsheet_id}
        response = requests.post(URL.DELETE_CHEATSHEET.value, data=payload)
        self._compare_num_cheatsheets(response, 0)
        assert self._count_cheatsheets_in_db() == 0
        assert response.text.count(app.DELETE_CHEATSHEET_OK_MSG) == 1

    def test_delete_2_cheatsheets_success(self):
        for _ in range(5):
            self._add_cheatsheet_to_db("test_snippet", "test_section")
        assert self._count_cheatsheets_in_db() == 5

        cheatsheet_id = 2
        payload = {"cheatsheet_id": cheatsheet_id}
        response = requests.post(URL.DELETE_CHEATSHEET.value, data=payload)
        self._compare_num_cheatsheets(response, 4)
        assert self._count_cheatsheets_in_db() == 4
        assert response.text.count(app.DELETE_CHEATSHEET_OK_MSG) == 1

        cheatsheet_id = 4
        payload = {"cheatsheet_id": cheatsheet_id}
        response = requests.post(URL.DELETE_CHEATSHEET.value, data=payload)
        self._compare_num_cheatsheets(response, 3)
        assert self._count_cheatsheets_in_db() == 3
        assert response.text.count(app.DELETE_CHEATSHEET_OK_MSG) == 1

    def test_delete_cheatsheet_fail(self):
        self._add_cheatsheet_to_db("test_snippet", "test_section")
        assert self._count_cheatsheets_in_db() == 1

        cheatsheet_id = 1234
        payload = {"cheatsheet_id": cheatsheet_id}
        response = requests.post(URL.DELETE_CHEATSHEET.value, data=payload)
        self._compare_num_cheatsheets(response, 1)
        assert self._count_cheatsheets_in_db() == 1
        assert response.text.count(app.DELETE_CHEATSHEET_ERR_MSG) == 1

    def test_delete_cheatsheet_fail_no_db(self):
        # delete the db in order to get an internal error.
        self._delete_db()

        cheatsheet_id = 1
        payload = {"cheatsheet_id": cheatsheet_id}
        response = requests.post(URL.DELETE_CHEATSHEET.value, data=payload)
        self._compare_num_cheatsheets(response, 0, db_avail=False)
        assert response.text.count(app.DELETE_CHEATSHEET_ERR_MSG) == 1
        assert response.text.count(app.GET_CHEATSHEETS_ERR_MSG) == 1
