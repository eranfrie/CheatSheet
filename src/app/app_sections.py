class DisplayCheatsheetsSection:
    """
    Args:
        cheatsheets (list(Cheatsheet) | None):
            list of cheatsheets to be display.
            None if error occured.
        display_cheatsheets_err (str | None):
            message to be displayed in case of error
            when trying to fetch the cheatsheets.
    """
    def __init__(self, cheatsheets, display_cheatsheets_err):
        self.cheatsheets = cheatsheets
        self.display_cheatsheets_err = display_cheatsheets_err


class CheatsheetSection:
    """
    Args:
        last_snippet (str | ""): snippet to be displayed in the "add cheatsheet" input field.
            empty string ("") to display the placeholder.
        last_section (str | ""): section to be displayed in the "add cheatsheet" input field.
            empty string ("") to display the placeholder.
        snippet_id: relevant only if it's an edit form, otherwise None
        preview_snippet: relevant only if it's an edit form, otherwise None
    """
    def __init__(self, last_snippet, last_section, snippet_id, preview_snippet):
        self.last_snippet = last_snippet
        self.last_section = last_section
        self.snippet_id = snippet_id
        self.preview_snippet = preview_snippet


class StatusSection:
    def __init__(self, success, msg):
        self.success = success
        self.msg = msg
