from utils import html_utils


# pylint: disable=R0201 (no-self-use)
class TestHTMLUtils:
    def test_html_escape(self):
        assert html_utils.html_escape("<>") == "&lt;&gt;"
        assert html_utils.html_escape("&") == "&amp;"
        assert html_utils.html_escape("") == ""
        assert html_utils.html_escape(None) is None

    def test_split_escaped_text(self):
        assert not html_utils.split_escaped_text("")

        assert html_utils.split_escaped_text("a") == ["a"]
        assert html_utils.split_escaped_text("ab") == ["a", "b"]
        assert html_utils.split_escaped_text("&lt;ab") == ["&lt;", "a", "b"]
        assert html_utils.split_escaped_text("ab&gt;") == ["a", "b", "&gt;"]
        assert html_utils.split_escaped_text("a&amp;b") == ["a", "&amp;", "b"]
