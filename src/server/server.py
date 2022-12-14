import logging

from server.cheatsheet import Cheatsheet
from server.server_api import InternalException, SnippetRequiredException


logger = logging.getLogger()


class Server:
    def __init__(self, db):
        self.db = db
        self._cache = None

    def _invalidate_cache(self):
        logger.debug("invalidating cache")
        self._cache = None

    def _get_all_cheatsheets(self):
        """
        Returns:
            list of Cheatsheet objects
        """
        # don't use cache if cache is None -
        #     it means either cache was invalidated or an error occurred in previous call
        #     if an error occurred in previous call - we want to try again this time
        # or if cache size is 0 -
        #     mainly for tests (and it's not an interesting case to cache)
        if self._cache:
            return self._cache

        cheatsheets = []

        try:
            cheatsheets_json = self.db.read_all_cheatsheets()
        except Exception as e:
            logger.exception("failed to read cheatsheets from db")
            raise InternalException() from e

        for j in cheatsheets_json:
            section = j["section"] if j["section"] else ""
            section = section.lower()  # ignore case
            cheatsheets.append(
                Cheatsheet(
                    j["id"],
                    j["snippet"],
                    section,
                )
            )

        cheatsheets.sort()
        self._cache = cheatsheets
        return self._cache

    def get_cheatsheets(self, pattern, is_fuzzy):
        cheatsheets = self._get_all_cheatsheets()
        if not pattern:
            return cheatsheets

        pattern = pattern.lower()
        return [b for b in cheatsheets if b.match(pattern, is_fuzzy)]

    def add_cheatsheet(self, snippet, section):
        self._invalidate_cache()

        # strip input
        snippet = "" if snippet is None else snippet.strip()
        section = "" if section is None else section.strip()

        # input validation
        if not snippet:
            logger.debug("add cheatsheet failed - snippet is required")
            raise SnippetRequiredException()

        try:
            self.db.add_cheatsheet(snippet, section)
            logger.info("cheatsheet added successfully")
        except Exception as e:
            logger.exception("failed to add cheatsheet to db: snippet=%s, section=%s", snippet, section)
            raise InternalException() from e

    def delete_cheatsheet(self, cheatsheet_id):
        """
        Returns:
            bool: whether delete succeeded or not
        """
        self._invalidate_cache()

        try:
            logger.info("requested to delete cheatsheet_id %s", cheatsheet_id)
            cheatsheet_id = int(cheatsheet_id)
            return self.db.delete_cheatsheet(cheatsheet_id)
        # pylint: disable=W0703 (broad-except)
        except Exception:
            logger.exception("failed to delete cheatsheet_id %s", cheatsheet_id)
            return False
