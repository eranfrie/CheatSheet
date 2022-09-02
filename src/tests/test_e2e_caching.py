import requests

from tests.test_e2e_base import TestE2eBase, URL


class TestE2eCaching(TestE2eBase):
    def test_cache(self):
        # add a cheatsheet
        response = self._add_cheatsheet("test_snippet", "test_section")
        self._compare_num_cheatsheets(response, 1)

        # add a cheatsheet directly to the DB
        # but still get one cheatsheet (cached)
        self._add_cheatsheet_to_db("test_snippet", "test_section")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 1, db_avail=False)

    def test_invalidate_cache(self):
        # add a cheatsheet directly to DB
        self.test_cache()

        # add a cheatsheet via API - cache should be invalidated
        response = self._add_cheatsheet("test_snippet", "test_section")
        self._compare_num_cheatsheets(response, 3)

    def test_cache_delted_db(self):
        response = self._add_cheatsheet("test_snippet", "test_section")
        self._compare_num_cheatsheets(response, 1)

        self._delete_db()

        # should get cached cheatsheets
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 1, db_avail=False)

    def test_empty_db_no_cache(self):
        # get 0 cheatsheets
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 0)

        # making sure cache is not used after getting 0 cheatsheets
        # by adding a cheatsheet directly to Db and sending GET again
        self._add_cheatsheet_to_db("test_snippet", "test_section")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 1)
