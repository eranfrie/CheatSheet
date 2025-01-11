import logging

from server.cheatsheet import Cheatsheet
from server.server_api import InternalException, SnippetRequiredException
from server.semantic_search import SemanticSearch
from server.gen_ai import GenAI


logger = logging.getLogger()


class Server:
    def __init__(self, db, enable_ai):
        self.db = db
        self._cache = None
        if enable_ai:
            self._semantic_search = SemanticSearch()
            self._gen_ai = GenAI()

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
            cheatsheets.append(Cheatsheet.from_json(j))

        cheatsheets.sort()
        self._cache = cheatsheets
        return self._cache

    def get_cheatsheets(self, patterns, is_fuzzy, favorites_only):
        cheatsheets = self._get_all_cheatsheets()

        if favorites_only:
            cheatsheets = [c for c in cheatsheets if c.is_favorited]

        if not patterns:
            return cheatsheets

        matches = cheatsheets
        patterns = [p.lower() for p in patterns]
        for p in patterns:
            matches = [m for m in matches if m.match(p, is_fuzzy)]
        return matches

    def perform_semantic_search(self, search_res_idx, query):
        cheatsheets = self._get_all_cheatsheets()
        if not cheatsheets:
            return None

        # check we are not out of boundary
        if search_res_idx < 0:
            search_res_idx = 0
        elif search_res_idx >= len(cheatsheets):
            search_res_idx = len(cheatsheets) - 1

        snippets = [c.snippet for c in cheatsheets]
        most_similar_idx = self._semantic_search.get_similar_cheatsheet(search_res_idx, query, snippets)
        cheatsheet = cheatsheets[most_similar_idx]

        # generate an answer to the query based on the semantic search result
        generated_answer = self._gen_ai.generate_answer(cheatsheet.snippet, query)

        return search_res_idx, cheatsheet.id, cheatsheet.snippet, generated_answer

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
            self.db.add_cheatsheet(snippet, section, False)
            logger.info("cheatsheet added successfully")
        except Exception as e:
            logger.exception("failed to add cheatsheet to db: snippet=%s, section=%s", snippet, section)
            raise InternalException() from e

    def get_cheatsheet(self, cheatsheet_id):
        """
        Returns:
            str if cheatsheet exists or None
        """
        try:
            cheatsheet_id = int(cheatsheet_id)
            j = self.db.read_cheatsheet(cheatsheet_id)
            return Cheatsheet.from_json(j)
        # pylint: disable=W0703 (broad-except)
        except Exception:
            logger.exception("failed to get cheatsheet_id %s", cheatsheet_id)
            return None

    def edit_cheatsheet(self, snippet_id, snippet, section):
        self._invalidate_cache()

        # strip input
        snippet = "" if snippet is None else snippet.strip()
        section = "" if section is None else section.strip()

        # input validation
        if not snippet:
            logger.debug("edit cheatsheet failed - snippet is required")
            raise SnippetRequiredException()

        try:
            self.db.edit_cheatsheet(snippet_id, snippet, section)
            logger.info("cheatsheet edited successfully")
        except Exception as e:
            logger.exception("failed to update cheatsheet in db: snippet_id=%s, snippet=%s, section=%s",
                             snippet_id, snippet, section)
            raise InternalException() from e

    def toggle_favorited(self, cheatsheet_id):
        self._invalidate_cache()

        return self.db.toggle_favorited(cheatsheet_id)

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
