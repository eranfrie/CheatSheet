import logging

from server.server_api import InternalException
from server.bookmarks import html_escape
from app.app_sections import DisplayBookmarksSection, AddBookmarkSection


GET_BOOKMARKS_ERR_MSG = "Internal error. Please try again later"
ADD_BOOKMARK_ERR_MSG = "Internal error: Failed to add a new bookmark. Please try again later"
ADD_BOOKMARK_OK_MSG = "Bookmark added successfully"
ADD_BOOKMARK_TITLE_REQUIRED_MSG = "Error: Title is a required field"
ADD_BOOKMARK_URL_REQUIRED_MSG = "Error: URL is a required field"

logger = logging.getLogger()


class App:
    def __init__(self, server):
        self.server = server

    def _main_page(self, add_bookmarks_section):
        """Returns all information to be displayed in the main page.

        Args:
            add_bookmarks_section: DisplayBookmarksSection object

        Returns:
            display_bookmarks_section:
                DisplayBookmarksSection object
            escaped_add_bookmarks_section:
                AddBookmarkSection object after escaping the relevant fields
        """
        try:
            bookmarks = self.server.get_all_bookmarks()
            display_bookmarks_section = DisplayBookmarksSection(bookmarks, None)
        except InternalException:
            display_bookmarks_section = DisplayBookmarksSection(None, GET_BOOKMARKS_ERR_MSG)

        # escape add_bookmarks_section
        escaped_add_bookmarks_section = AddBookmarkSection(
            add_bookmarks_section.last_op_succeeded,
            add_bookmarks_section.last_op_msg,
            html_escape(add_bookmarks_section.last_title),
            html_escape(add_bookmarks_section.last_description),
            html_escape(add_bookmarks_section.last_url)
        )

        return display_bookmarks_section, escaped_add_bookmarks_section

    def display_bookmarks(self):
        """
        Returns all information needed to display the main page
        (see `_main_page` function).
        """
        add_bookmarks_section = AddBookmarkSection(None, None, "", "", "")
        return self._main_page(add_bookmarks_section)

    def add_bookmark(self, title, description, url):
        """
        Returns all information needed to display the main page
        (see `_main_page` function).
        """
        logger.info("got request to add bookmark: title=%s, desc=%s, url=%s",
                    title, description, url)

        # input validation
        # not expected to happen because browser enforces it
        # (using HTML 'required' attribute)
        if not title or not url:
            add_bookmark_msg = ADD_BOOKMARK_TITLE_REQUIRED_MSG if not title \
                    else ADD_BOOKMARK_URL_REQUIRED_MSG
            add_bookmarks_section = AddBookmarkSection(False, add_bookmark_msg, title, description, url)
            return self._main_page(add_bookmarks_section)

        try:
            self.server.add_bookmark(title, description, url)
            add_bookmarks_section = AddBookmarkSection(True, ADD_BOOKMARK_OK_MSG, "", "", "")
            return self._main_page(add_bookmarks_section)
        except InternalException:
            add_bookmarks_section = AddBookmarkSection(False, ADD_BOOKMARK_ERR_MSG, title, description, url)
            return self._main_page(add_bookmarks_section)
