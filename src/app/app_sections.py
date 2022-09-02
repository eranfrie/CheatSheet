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


class AddCheatsheetSection:
    """
    Args:
        last_op_succeeded (bool | None):
            True/False if adding a cheatsheet is being requested and succeeded/failed accordingly.
            None if adding a cheatsheet is not being requested.
        last_op_msg (str | None):
            if last_op_succeeded is True/False, a message to display.
        last_snippet (str | ""): snippet to be displayed in the "add cheatsheet" input field.
            empty string ("") to display the placeholder.
        last_section (str | ""): section to be displayed in the "add cheatsheet" input field.
            empty string ("") to display the placeholder.
    """
    def __init__(self, last_snippet, last_section):
        self.last_snippet = last_snippet
        self.last_section = last_section


class StatusSection:
    def __init__(self, success, msg):
        self.success = success
        self.msg = msg
