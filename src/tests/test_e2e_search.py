import requests

from tests.test_e2e_base import TestE2eBase, URL


class TestE2eSearch(TestE2eBase):
    def test_complete_match_title(self):
        self._add_bookmark_to_db("test_title_1", "test_section_1")
        self._add_bookmark_to_db("test_title_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 2)

        pattern = "test_title_1"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_bookmarks(response, 1, db_avail=False)

    def test_fuzzy_title(self):
        self._add_bookmark_to_db("test_title_1", "test_section_1")
        self._add_bookmark_to_db("test_title_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 2)

        pattern = "testtitle1"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_bookmarks(response, 1, db_avail=False)

    def test_fuzzy_ignore_case_title(self):
        self._add_bookmark_to_db("test_title_1", "test_section_1")
        self._add_bookmark_to_db("test_title_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 2)

        pattern = "TESTtitle1"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_bookmarks(response, 1, db_avail=False)

    def test_html_escaping_title(self):
        self._add_bookmark_to_db("<>test_title_1", "test_section_1")
        self._add_bookmark_to_db("<>test_title_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 2)

        pattern = "<>TESTtitle1"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_bookmarks(response, 1, db_avail=False)

    def test_sql_escaping_title(self):
        self._add_bookmark_to_db("\"'test_title_1", "test_section_1")
        self._add_bookmark_to_db("\"'test_title_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 2)

        pattern = "\"'TESTtitle1"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_bookmarks(response, 1, db_avail=False)

    def test_clear_search_no_highlight(self):
        self._add_bookmark_to_db("test_title_1", "test_section_1")
        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 1)

        pattern = "test_title_1"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_bookmarks(response, 1)

        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 1)

    def test_highlight_section(self):
        self._add_bookmark_to_db("test_highlight", "test_highlight")
        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 1)

        pattern = "testhghlgt"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_bookmarks(response, 1)

    def test_regular_search(self):
        self._add_bookmark_to_db("test_title_1", "test_section_1")
        self._add_bookmark_to_db("test_title_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 2)

        pattern = "test_title_1"
        params = {"pattern": pattern, "fuzzy": "true"}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_bookmarks(response, 1, db_avail=False)

    def test_regular_search_no_match(self):
        self._add_bookmark_to_db("test_title_1", "test_section_1")
        self._add_bookmark_to_db("test_title_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 2)

        pattern = "tsttitle1"
        params = {"pattern": pattern, "fuzzy": "false"}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_bookmarks(response, 0, db_avail=False)
