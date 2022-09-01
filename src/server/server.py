import logging

from server.bookmark import Bookmark
from server.server_api import InternalException, TitleRequiredException


logger = logging.getLogger()


class Server:
    def __init__(self, db):
        self.db = db
        self._cache = None

    def _invalidate_cache(self):
        logger.debug("invalidating cache")
        self._cache = None

    def _get_all_bookmarks(self):
        """
        Returns:
            list of Bookmark objects
        """
        # don't use cache if cache is None -
        #     it means either cache was invalidated or an error occurred in previous call
        #     if an error occurred in previous call - we want to try again this time
        # or if cache size is 0 -
        #     mainly for tests (and it's not an interesting case to cache)
        if self._cache:
            return self._cache

        bookmarks = []

        try:
            bookmarks_json = self.db.read_all_bookmarks()
        except Exception as e:
            logger.exception("failed to read bookmarks from db")
            raise InternalException() from e

        for j in bookmarks_json:
            section = j["section"] if j["section"] else ""
            section = section.lower()  # ignore case
            bookmarks.append(
                Bookmark(
                    j["id"],
                    j["title"],
                    section,
                )
            )

        bookmarks.sort()
        self._cache = bookmarks
        return self._cache

    def get_bookmarks(self, pattern, is_fuzzy):
        bookmarks = self._get_all_bookmarks()
        if not pattern:
            return bookmarks

        pattern = pattern.lower()
        return [b for b in bookmarks if b.match(pattern, is_fuzzy)]

    def add_bookmark(self, title, section):
        self._invalidate_cache()

        # strip input
        title = "" if title is None else title.strip()
        section = "" if section is None else section.strip()

        # input validation
        if not title:
            logger.debug("add bookmark failed - title is required")
            raise TitleRequiredException()

        try:
            self.db.add_bookmark(title, section)
            logger.info("bookmark added successfully")
        except Exception as e:
            logger.exception("failed to add bookmark to db: title=%s, section=%s",
                             title, section)
            raise InternalException() from e

    def delete_bookmark(self, bookmark_id):
        """
        Returns:
            bool: whether delete succeeded or not
        """
        self._invalidate_cache()

        try:
            logger.info("requested to delete bookmark_id %s", bookmark_id)
            bookmark_id = int(bookmark_id)
            return self.db.delete_bookmark(bookmark_id)
        # pylint: disable=W0703 (broad-except)
        except Exception:
            logger.exception("failed to delete bookmark_id %s", bookmark_id)
            return False
