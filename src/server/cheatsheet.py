from utils.html_utils import html_escape, split_escaped_text
from server.fuzzy_search import is_match


def _regular_search(pattern, text):
    """
    Assumptions:
        pattern is not None
        pattern is lower case
        text is lower case

    Returns:
        indexes (set) of matched indexes
            if pattern is contained in text
        None otherwise
    """
    for line in text.splitlines():
        try:
            first_indes = line.index(pattern)
            return set(range(first_indes, first_indes + len(pattern)))
        except ValueError:
            continue

    return None


# pylint: disable=R0902 (too-many-instance-attributes)
class Cheatsheet:
    @classmethod
    def from_json(cls, j):
        section = j["section"] if j["section"] else ""
        section = section.lower()  # ignore case
        return Cheatsheet(
            j["id"],
            j["snippet"],
            section,
            j["is_favorited"],
        )

    # pylint: disable=R0913 (too-many-arguments)
    def __init__(self, cheatsheet_id, snippet, section, is_favorited):
        self.id = cheatsheet_id
        self.snippet = snippet if snippet else ""
        self.section = section.lower() if section else ""  # section always lower case
        self.is_favorited = is_favorited

        # don't be sensitive around / separators
        sub_sections = self.section.split("/")
        sub_sections = [s.strip() for s in sub_sections]
        self.section = " / ".join(sub_sections)

        self.snippet_lower = self.snippet.lower()
        self.section_lower = self.section.lower()

        self.escaped_snippet = html_escape(self.snippet)
        self.escaped_section = html_escape(self.section)

        self.escaped_chars_snippet = split_escaped_text(self.escaped_snippet)
        assert len(self.escaped_chars_snippet) == len(self.snippet)
        self.escaped_chars_section = split_escaped_text(self.escaped_section)
        assert len(self.escaped_chars_section) == len(self.section)

    def __lt__(self, other):
        if self.section_lower != other.section_lower:
            return self.section_lower < other.section_lower
        return self.snippet_lower < other.snippet_lower

    def match(self, pattern, is_fuzzy):
        """
        Assumptions:
            pattern is not None
            pattern is lower case
        """
        search_method = is_match if is_fuzzy else _regular_search
        return search_method(pattern, self.snippet_lower) is not None
