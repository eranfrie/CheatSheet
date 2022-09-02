class DisplayBookmarksSection:
    """
    Args:
        bookmarks (list(Bookmark) | None):
            list of bookmarks to be display.
            None if error occured.
        display_bookmarks_err (str | None):
            message to be displayed in case of error
            when trying to fetch the bookmarks.
    """
    def __init__(self, bookmarks, display_bookmarks_err):
        self.bookmarks = bookmarks
        self.display_bookmarks_err = display_bookmarks_err


class AddBookmarkSection:
    """
    Args:
        last_op_succeeded (bool | None):
            True/False if adding a bookmark is being requested and succeeded/failed accordingly.
            None if adding a bookmark is not being requested.
        last_op_msg (str | None):
            if last_op_succeeded is True/False, a message to display.
        last_snippet (str | ""): snippet to be displayed in the "add bookmark" input field.
            empty string ("") to display the placeholder.
        last_section (str | ""): section to be displayed in the "add bookmark" input field.
            empty string ("") to display the placeholder.
    """
    def __init__(self, last_snippet, last_section):
        self.last_snippet = last_snippet
        self.last_section = last_section


class StatusSection:
    def __init__(self, success, msg):
        self.success = success
        self.msg = msg
