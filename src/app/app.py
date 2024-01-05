import logging

from utils.html_utils import html_escape
from server.server_api import InternalException, SnippetRequiredException
from app.app_sections import DisplayCheatsheetsSection, CheatsheetSection, StatusSection


GET_CHEATSHEETS_ERR_MSG = "Internal error. Please try again later"
ADD_CHEATSHEET_ERR_MSG = "Internal error: Failed to add a new snippet. Please try again later"
ADD_CHEATSHEET_OK_MSG = "Snippet added successfully"
SNIPPET_REQUIRED_MSG = "Error: Snippet is a required field"
EDIT_CHEATSHEET_ERR_MSG = "Internal error: Failed to edit a snippet. Please try again later"
EDIT_CHEATSHEET_OK_MSG = "Snippet edited successfully"

DELETE_CHEATSHEET_OK_MSG = "Snippet deleted successfully"
DELETE_CHEATSHEET_ERR_MSG = "Failed to delete snippet"


logger = logging.getLogger()


class App:
    def __init__(self, server):
        self.server = server

    def display_cheatsheets(self, patterns, is_fuzzy):
        """
        Args:
            pattern (str | None): a pattern to filter results
            is_fuzzy (bool): whether to perform a fuzzy search or regular search

        Returns:
            display_cheatsheets_section: DisplayCheatsheetsSection object
        """
        try:
            cheatsheets = self.server.get_cheatsheets(patterns, is_fuzzy)
            return DisplayCheatsheetsSection(cheatsheets, None)
        except InternalException:
            return DisplayCheatsheetsSection(None, GET_CHEATSHEETS_ERR_MSG)

    def add_cheatsheet(self, snippet, section):
        logger.info("got request to add cheatsheet: snippet=%s, section=%s",
                    snippet, section)

        try:
            self.server.add_cheatsheet(snippet, section)
            cheatsheet_section = CheatsheetSection("", "", None)
            status_section = StatusSection(True, ADD_CHEATSHEET_OK_MSG)
        except InternalException:
            cheatsheet_section = CheatsheetSection(snippet, section, None)
            status_section = StatusSection(False, ADD_CHEATSHEET_ERR_MSG)
        except SnippetRequiredException:
            cheatsheet_section = CheatsheetSection(snippet, section, None)
            status_section = StatusSection(False, SNIPPET_REQUIRED_MSG)

        # escape cheatsheet_section
        escaped_cheatsheets_section = CheatsheetSection(
            html_escape(cheatsheet_section.last_snippet),
            html_escape(cheatsheet_section.last_section),
            None
        )

        return status_section, self.display_cheatsheets(None, None), escaped_cheatsheets_section

    def edit_cheatsheet_form(self, cheatsheet_id):
        return self.server.get_cheatsheet(cheatsheet_id)

    def edit_cheatsheet(self, snippet_id, snippet, section):
        logger.info("got request to edit cheatsheet: snippet_id=%s, snippet=%s, section=%s",
                    snippet_id, snippet, section)

        try:
            self.server.edit_cheatsheet(snippet_id, snippet, section)
            cheatsheet_section = CheatsheetSection("", "", None)
            status_section = StatusSection(True, EDIT_CHEATSHEET_OK_MSG)
        except InternalException:
            cheatsheet_section = CheatsheetSection(snippet, section, None)
            status_section = StatusSection(False, EDIT_CHEATSHEET_ERR_MSG)
            return status_section, None, None
        except SnippetRequiredException:
            cheatsheet_section = CheatsheetSection(snippet, section, None)
            status_section = StatusSection(False, SNIPPET_REQUIRED_MSG)
            return status_section, None, None

        # escape cheatsheet_section
        escaped_cheatsheets_section = CheatsheetSection(
            html_escape(cheatsheet_section.last_snippet),
            html_escape(cheatsheet_section.last_section),
            None
        )

        return status_section, self.display_cheatsheets(None, None), escaped_cheatsheets_section

    def delete_cheatsheet(self, cheatsheet_id):
        if self.server.delete_cheatsheet(cheatsheet_id):
            status_section = StatusSection(True, DELETE_CHEATSHEET_OK_MSG)
        else:
            logger.error("failed to delete cheatsheet %s", cheatsheet_id)
            status_section = StatusSection(False, DELETE_CHEATSHEET_ERR_MSG)

        return status_section, self.display_cheatsheets(None, None)
