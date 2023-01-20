import logging
import sqlite3


logger = logging.getLogger()

CHEATSHEETS_TABLE = "snippets"


def sql_escape(text):
    if not text:
        return text
    return text.replace("'", "''")


def record_to_json(record):
    return {
        "id": record[0],
        "section": record[1],
        "snippet": record[2],
    }


class Sqlite:
    def __init__(self, db_filename):
        self.db_filename = db_filename
        logger.info("DB filename = %s", self.db_filename)

        self._create_tables_if_not_exists()

    def _connect(self):
        conn = sqlite3.connect(self.db_filename)
        return conn, conn.cursor()

    @classmethod
    def _close(cls, conn):
        conn.commit()
        conn.close()

    def _create_tables_if_not_exists(self):
        conn, cursor = self._connect()
        cheatsheets_table = \
            f"CREATE TABLE IF NOT EXISTS {CHEATSHEETS_TABLE} (" \
            "id integer PRIMARY KEY," \
            "section text," \
            "snippet text NOT NULL" \
            ");"
        cursor.execute(cheatsheets_table)
        Sqlite._close(conn)

    def read_all_cheatsheets(self):
        """
        Returns:
            list of dict (each dict is a record from the db)
        """
        conn, cursor = self._connect()
        cheatsheets = []

        try:
            records = cursor.execute(f"SELECT * FROM {CHEATSHEETS_TABLE};")
        except Exception as e:
            Sqlite._close(conn)
            raise e

        for record in records:
            cheatsheets.append(record_to_json(record))
        Sqlite._close(conn)
        return cheatsheets

    def read_cheatsheet(self, cheatsheet_id):
        """
        Returns:
            dict: a record from the db
        """
        conn, cursor = self._connect()

        try:
            records = cursor.execute(f"SELECT * FROM {CHEATSHEETS_TABLE} where id={cheatsheet_id};")
        except Exception as e:
            Sqlite._close(conn)
            raise e

        cheatsheet = None
        for record in records:  # only one record will be found
            cheatsheet = record_to_json(record)
        Sqlite._close(conn)
        return cheatsheet

    def add_cheatsheet(self, snippet, section):
        conn, cursor = self._connect()
        try:
            cursor.execute(f"INSERT INTO {CHEATSHEETS_TABLE} (section, snippet) "
                           f"VALUES ('{sql_escape(section)}', "
                           f"'{sql_escape(snippet)}');")
        finally:
            Sqlite._close(conn)

    def edit_cheatsheet(self, snippet_id, snippet, section):
        conn, cursor = self._connect()
        try:
            cursor.execute(f"UPDATE {CHEATSHEETS_TABLE} "
                           f"SET section='{sql_escape(section)}', "
                           f"snippet='{sql_escape(snippet)}' "
                           f"WHERE id={snippet_id};")
        finally:
            Sqlite._close(conn)

    def delete_cheatsheet(self, cheatsheet_id):
        """
        Args:
            cheatsheet_id (int): no need to escapse
        """
        rows_deleted = 0
        conn, cursor = self._connect()
        try:
            cursor.execute(f"DELETE FROM {CHEATSHEETS_TABLE} WHERE id=?;", (cheatsheet_id, ))
            rows_deleted = cursor.rowcount
        finally:
            Sqlite._close(conn)
        return rows_deleted == 1
