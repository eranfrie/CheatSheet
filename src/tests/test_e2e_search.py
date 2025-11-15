import requests

from tests.test_e2e_base import TestE2eBase, URL


class TestE2eSearch(TestE2eBase):
    def test_complete_match_snippet(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        self._add_cheatsheet_to_db("test_snippet_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 2)

        pattern = "test_snippet_1"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_cheatsheets(response, 1, db_avail=False)

    def test_fuzzy_snippet(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        self._add_cheatsheet_to_db("test_snippet_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 2)

        pattern = "testsnppt"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_cheatsheets(response, 1, db_avail=False)

    def test_fuzzy_ignore_case_snippet(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        self._add_cheatsheet_to_db("test_snippet_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 2)

        pattern = "TESTsnppt"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_cheatsheets(response, 1, db_avail=False)

    def test_html_escaping_snippet(self):
        self._add_cheatsheet_to_db("<>test_snippet_1", "test_section_1")
        self._add_cheatsheet_to_db("<>test_snippet_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 2)

        pattern = "<>TESTsnppt1"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_cheatsheets(response, 1, db_avail=False)

    def test_sql_escaping_snippet(self):
        self._add_cheatsheet_to_db("\"'test_snippet_1", "test_section_1")
        self._add_cheatsheet_to_db("\"'test_snippet_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 2)

        pattern = "\"'TESTsnppt1"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_cheatsheets(response, 1, db_avail=False)

    def test_clear_search_no_highlight(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 1)

        pattern = "test_snippet_1"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_cheatsheets(response, 1)

        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 1)

    def test_highlight_section(self):
        self._add_cheatsheet_to_db("test_highlight", "test_highlight")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 1)

        pattern = "testhghlgt"
        params = {"pattern": pattern}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_cheatsheets(response, 1)

    def test_regular_search(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        self._add_cheatsheet_to_db("test_snippet_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 2)

        pattern = "test_snippet_1"
        params = {"pattern": pattern, "fuzzy": "true"}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_cheatsheets(response, 1, db_avail=False)

    def test_regular_search_no_match(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        self._add_cheatsheet_to_db("test_snippet_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 2)

        pattern = "tstsnppt1"
        params = {"pattern": pattern, "fuzzy": "false"}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_cheatsheets(response, 0, db_avail=False)

    def test_section_filter_only(self):
        self._add_cheatsheet_to_db("test_snippet_1", "test_section_1")
        self._add_cheatsheet_to_db("test_snippet_2", "test_section_2")
        self._add_cheatsheet_to_db("test_snippet_3", "test_section_3")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 3)

        params = {"sectionPattern": "test_section_1"}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_cheatsheets(response, 1, db_avail=False)

    def test_section_filter_case_insensitive(self):
        self._add_cheatsheet_to_db("test_snippet_1", "TEST_SECTION_1")
        self._add_cheatsheet_to_db("test_snippet_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 2)

        params = {"sectionPattern": "test_section_1"}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_cheatsheets(response, 1, db_avail=False)

    def test_section_filter_with_pattern(self):
        self._add_cheatsheet_to_db("test_snippet_1", "TEST_SECTION_1")
        self._add_cheatsheet_to_db("test_snippet_2", "test_section_2")
        self._add_cheatsheet_to_db("test_snippet_3", "test_section_3")

        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 3)

        # Filter by section and pattern
        pattern = "snippet_1"
        params = {"pattern": pattern, "sectionPattern": "test_section_1"}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_cheatsheets(response, 1, db_avail=False)

    def test_section_filter_no_match(self):
        self._add_cheatsheet_to_db("test_snippet_1", "TEST_SECTION_1")
        self._add_cheatsheet_to_db("test_snippet_2", "test_section_2")
        response = requests.get(URL.INDEX.value)
        self._compare_num_cheatsheets(response, 2)

        params = {"sectionPattern": "nonexistent_section"}
        response = requests.get(URL.INDEX.value, params=params)
        self._compare_num_cheatsheets(response, 0, db_avail=False)
