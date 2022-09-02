import logging

from utils.html_utils import html_escape
from server.server_api import InternalException, TitleRequiredException
from app.app_sections import DisplayBookmarksSection, AddBookmarkSection, StatusSection


GET_BOOKMARKS_ERR_MSG = "Internal error. Please try again later"
ADD_BOOKMARK_ERR_MSG = "Internal error: Failed to add a new snippet. Please try again later"
ADD_BOOKMARK_OK_MSG = "Snippet added successfully"
ADD_BOOKMARK_TITLE_REQUIRED_MSG = "Error: Snippet is a required field"

DELETE_BOOKMARK_OK_MSG = "Snippet deleted successfully"
DELETE_BOOKMARK_ERR_MSG = "Failed to delete snippet"


logger = logging.getLogger()


class App:
    def __init__(self, server):
        self.server = server

    def display_bookmarks(self, pattern, is_fuzzy):
        """
        Args:
            pattern (str | None): a pattern to filter results
            is_fuzzy (bool): whether to perform a fuzzy search or regular search

        Returns:
            display_bookmarks_section: DisplayBookmarksSection object
        """
        try:
            bookmarks = self.server.get_bookmarks(pattern, is_fuzzy)

            # clean last search
            if not pattern:
                for b in bookmarks:
                    if b.title_indexes:
                        b.title_indexes.clear()
                    if b.section_indexes:
                        b.section_indexes.clear()

            return DisplayBookmarksSection(bookmarks, None)
        except InternalException:
            return DisplayBookmarksSection(None, GET_BOOKMARKS_ERR_MSG)

    def add_bookmark(self, title, section):
        logger.info("got request to add bookmark: title=%s, section=%s",
                    title, section)

        try:
            self.server.add_bookmark(title, section)
            add_bookmark_section = AddBookmarkSection("", "")
            status_section = StatusSection(True, ADD_BOOKMARK_OK_MSG)
        except InternalException:
            add_bookmark_section = AddBookmarkSection(title, section)
            status_section = StatusSection(False, ADD_BOOKMARK_ERR_MSG)
        except TitleRequiredException:
            add_bookmark_section = AddBookmarkSection(title, section)
            status_section = StatusSection(False, ADD_BOOKMARK_TITLE_REQUIRED_MSG)

        # escape add_bookmark_section
        escaped_add_bookmarks_section = AddBookmarkSection(
            html_escape(add_bookmark_section.last_title),
            html_escape(add_bookmark_section.last_section)
        )

        return status_section, self.display_bookmarks(None, None), escaped_add_bookmarks_section

    def delete_bookmark(self, bookmark_id):
        if self.server.delete_bookmark(bookmark_id):
            status_section = StatusSection(True, DELETE_BOOKMARK_OK_MSG)
        else:
            logger.error("failed to delete bookmark %s", bookmark_id)
            status_section = StatusSection(False, DELETE_BOOKMARK_ERR_MSG)

        return status_section, self.display_bookmarks(None, None)
