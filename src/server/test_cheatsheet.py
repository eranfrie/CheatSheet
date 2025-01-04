from server.cheatsheet import Cheatsheet


values = ["test", "Test_1", "", "Test", "", "test_1"]
sorted_values = ["", "", "test", "Test", "Test_1", "test_1"]


# pylint: disable=R0201 (no-self-use)
class TestFuzzySearch:
    def test_sort_by_section(self):
        cheatsheets = []
        for v in values:
            cheatsheets.append(
                Cheatsheet(1, "", v, False),
            )
        cheatsheets.sort()
        for v, b in zip(sorted_values, cheatsheets):
            assert v.lower() == b.section  # lower() because section is always lower

    def test_sort_by_snippet(self):
        cheatsheets = []
        for v in values:
            cheatsheets.append(
                Cheatsheet(1, v, "", False),
            )
        cheatsheets.sort()
        for v, b in zip(sorted_values, cheatsheets):
            assert v == b.snippet
