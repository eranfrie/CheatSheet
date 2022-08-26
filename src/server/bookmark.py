from utils.html_utils import html_escape, split_escaped_text
from server.fuzzy_search import is_match


def _regular_search(pattern, line):
    """
    Assumptions:
        pattern is not None
        pattern is lower case
        line is lower case

    Returns:
        indexes (set) of matched indexes
            if pattern is "fuzzy" contained in line
        None otherwise
    """
    try:
        first_indes = line.index(pattern)
    except ValueError:
        return None
    return set(range(first_indes, first_indes + len(pattern)))


# pylint: disable=R0902 (too-many-instance-attributes)
class Bookmark:
    # pylint: disable=R0913 (too-many-arguments)
    def __init__(self, bookmark_id, title, section):
        self.id = bookmark_id
        self.title = title if title else ""
        self.section = section.lower() if section else ""  # section always lower case

        # don't be sensitive around / separators
        sub_sections = self.section.split("/")
        sub_sections = [s.strip() for s in sub_sections]
        self.section = " / ".join(sub_sections)

        self.title_lower = self.title.lower()
        self.section_lower = self.section.lower()

        self.escaped_title = html_escape(self.title)
        self.escaped_section = html_escape(self.section)

        self.escaped_chars_title = split_escaped_text(self.escaped_title)
        assert len(self.escaped_chars_title) == len(self.title)
        self.escaped_chars_section = split_escaped_text(self.escaped_section)
        assert len(self.escaped_chars_section) == len(self.section)

        self.title_indexes = None
        self.section_indexes = None

    def __lt__(self, other):
        if self.section_lower != other.section_lower:
            return self.section_lower < other.section_lower
        return self.title_lower < other.title_lower

    def match(self, pattern, is_fuzzy, include_url):
        """
        Assumptions:
            pattern is not None
            pattern is lower case
        """
        search_method = is_match if is_fuzzy else _regular_search
        self.title_indexes = search_method(pattern, self.title_lower)
        self.section_indexes = search_method(pattern, self.section_lower)
        return self.title_indexes is not None or \
            self.description_indexes is not None or \
            (self.url_indexes is not None and include_url)
