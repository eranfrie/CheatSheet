from multiprocessing import Process
from pathlib import Path
from time import sleep
from enum import Enum

import requests

from main import main
from data import sqlite
from data.sqlite import Sqlite
from app.app_api import page_to_route, Route


OUTPUT_DIR = "tmp"
DB_FILENAME = "cheatsheet.db"
TEST_URL = "http://localhost:8000"
NUM_MENU_LINKS = len(page_to_route)


class URL (Enum):
    INDEX = TEST_URL + Route.INDEX.value
    CHEATSHEETS = TEST_URL + Route.CHEATSHEETS.value
    ADD_CHEATSHEET = TEST_URL + Route.ADD_CHEATSHEET.value
    DELETE_CHEATSHEET = TEST_URL + Route.DELETE_CHEATSHEET.value
    ABOUT = TEST_URL + Route.ABOUT.value


# pylint: disable=W0201, R0201 (attribute-defined-outside-init, no-self-use)
class TestE2eBase:
    def setup(self):
        # delete old db
        self._delete_db()

        # start the server
        override_config = {
            "output_dir": OUTPUT_DIR,
            "console_log_level": "WARNING",
        }
        self.server = Process(target=main, args=(override_config,))
        self.server.start()
        # wait for server to start
        for _ in range(120):
            try:
                r = requests.get(URL.INDEX.value)
                if r.status_code == 200:
                    return
            except requests.exceptions.ConnectionError:
                pass

            sleep(0.05)

        self.teardown()
        raise Exception("Server failed to start")

    def teardown(self):
        self.server.terminate()
        self.server.join()

    def _compare_num_cheatsheets(self, response, expected_num_cheatsheets, db_avail=True):
        assert response.status_code == 200
        if db_avail:
            assert f"Total: {expected_num_cheatsheets}" in response.text
            assert self._count_cheatsheets_in_db() == expected_num_cheatsheets

    def _add_cheatsheet_to_db(self, snippet, section):
        db_filename = Path(OUTPUT_DIR, DB_FILENAME)
        db = Sqlite(db_filename)
        db.add_cheatsheet(snippet, section)

    def _count_cheatsheets_in_db(self):
        db_filename = Path(OUTPUT_DIR, DB_FILENAME)
        db = Sqlite(db_filename)
        conn, cursor = db._connect()  # pylint: disable=W0212 (protected-access)
        res = cursor.execute(f"SELECT COUNT() FROM {sqlite.CHEATSHEETS_TABLE};")
        res = res.fetchone()[0]
        Sqlite._close(conn)  # pylint: disable=W0212 (protected-access)
        return res

    def _delete_db(self):
        try:
            Path(OUTPUT_DIR, DB_FILENAME).unlink()
        except FileNotFoundError:
            pass

    def _add_cheatsheet(self, snippet, section):
        payload = {}
        if snippet:
            payload["snippet"] = snippet
        if section:
            payload["section"] = section
        response = requests.post(URL.ADD_CHEATSHEET.value, data=payload)
        return response
