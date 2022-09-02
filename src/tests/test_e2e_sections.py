import re

import requests

from tests.test_e2e_base import TestE2eBase, URL


class TestE2eSections(TestE2eBase):
    def test_section_appears_once(self):
        """
        tests that links with the same section are grouped together
        and each section appears only once.
        """
        self._add_bookmark_to_db("test_snippet", "test_section_1")
        self._add_bookmark_to_db("test_snippet", "test_section_2")
        self._add_bookmark_to_db("test_snippet", "test_section_3")
        self._add_bookmark_to_db("test_snippet", "test_section_1")
        self._add_bookmark_to_db("test_snippet", "test_section_2")

        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 5)
        assert response.text.count("test_section_1") == 2
        assert response.text.count("test_section_2") == 2
        assert response.text.count("test_section_3") == 2

    def test_no_section_first(self):
        self._add_bookmark("test_snippet_3", "test_section_1")
        # special case - test that " " is treated as ""
        # so when sorting, it should come before the next bookmark (with "" section)
        self._add_bookmark("test_snippet_1", " ")
        self._add_bookmark("test_snippet_2", "")

        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 3)
        pattern = "test_snippet_1.*test_snippet_2.*test_section_1.*test_snippet_3"
        assert re.search(pattern, response.text)

    def test_section_ignore_case(self):
        self._add_bookmark_to_db("test_snippet", "Test_section")
        self._add_bookmark_to_db("test_snippet", "test_section")

        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 2)
        assert response.text.count("test_section") == 2

    def test_section_slash_separator(self):
        self._add_bookmark_to_db("test_snippet", "Test_section/sub_section")
        self._add_bookmark_to_db("test_snippet", "test_section / sub_section")
        self._add_bookmark_to_db("test_snippet", "test_section/ sub_section")
        self._add_bookmark_to_db("test_snippet", "test_section /sub_section")
        response = requests.get(URL.INDEX.value)
        self._compare_num_bookmarks(response, 4)
        assert response.text.count("test_section / sub_section") == 2
