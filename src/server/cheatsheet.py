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
        except ValueError:
            return None
        return set(range(first_indes, first_indes + len(pattern)))


# pylint: disable=R0902 (too-many-instance-attributes)
class Cheatsheet:
    # pylint: disable=R0913 (too-many-arguments)
    def __init__(self, cheatsheet_id, snippet, section):
        self.id = cheatsheet_id
        self.snippet = snippet if snippet else ""
        self.section = section.lower() if section else ""  # section always lower case

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

        self.snippet_indexes = None
        self.section_indexes = None

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
        self.snippet_indexes = search_method(pattern, self.snippet_lower)
        self.section_indexes = search_method(pattern, self.section_lower)
        return self.snippet_indexes is not None
