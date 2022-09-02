import logging

from utils.html_utils import html_escape
from server.server_api import InternalException, SnippetRequiredException
from app.app_sections import DisplayCheatsheetsSection, AddCheatsheetSection, StatusSection


GET_CHEATSHEETS_ERR_MSG = "Internal error. Please try again later"
ADD_CHEATSHEET_ERR_MSG = "Internal error: Failed to add a new snippet. Please try again later"
ADD_CHEATSHEET_OK_MSG = "Snippet added successfully"
ADD_CHEATSHEET_SNIPPET_REQUIRED_MSG = "Error: Snippet is a required field"

DELETE_CHEATSHEET_OK_MSG = "Snippet deleted successfully"
DELETE_CHEATSHEET_ERR_MSG = "Failed to delete snippet"


logger = logging.getLogger()


class App:
    def __init__(self, server):
        self.server = server

    def display_cheatsheets(self, pattern, is_fuzzy):
        """
        Args:
            pattern (str | None): a pattern to filter results
            is_fuzzy (bool): whether to perform a fuzzy search or regular search

        Returns:
            display_cheatsheets_section: DisplayCheatsheetsSection object
        """
        try:
            cheatsheets = self.server.get_cheatsheets(pattern, is_fuzzy)

            # clean last search
            if not pattern:
                for b in cheatsheets:
                    if b.snippet_indexes:
                        b.snippet_indexes.clear()
                    if b.section_indexes:
                        b.section_indexes.clear()

            return DisplayCheatsheetsSection(cheatsheets, None)
        except InternalException:
            return DisplayCheatsheetsSection(None, GET_CHEATSHEETS_ERR_MSG)

    def add_cheatsheet(self, snippet, section):
        logger.info("got request to add cheatsheet: snippet=%s, section=%s",
                    snippet, section)

        try:
            self.server.add_cheatsheet(snippet, section)
            add_cheatsheet_section = AddCheatsheetSection("", "")
            status_section = StatusSection(True, ADD_CHEATSHEET_OK_MSG)
        except InternalException:
            add_cheatsheet_section = AddCheatsheetSection(snippet, section)
            status_section = StatusSection(False, ADD_CHEATSHEET_ERR_MSG)
        except SnippetRequiredException:
            add_cheatsheet_section = AddCheatsheetSection(snippet, section)
            status_section = StatusSection(False, ADD_CHEATSHEET_SNIPPET_REQUIRED_MSG)

        # escape add_cheatsheet_section
        escaped_add_cheatsheets_section = AddCheatsheetSection(
            html_escape(add_cheatsheet_section.last_snippet),
            html_escape(add_cheatsheet_section.last_section)
        )

        return status_section, self.display_cheatsheets(None, None), escaped_add_cheatsheets_section

    def delete_cheatsheet(self, cheatsheet_id):
        if self.server.delete_cheatsheet(cheatsheet_id):
            status_section = StatusSection(True, DELETE_CHEATSHEET_OK_MSG)
        else:
            logger.error("failed to delete cheatsheet %s", cheatsheet_id)
            status_section = StatusSection(False, DELETE_CHEATSHEET_ERR_MSG)

        return status_section, self.display_cheatsheets(None, None)
