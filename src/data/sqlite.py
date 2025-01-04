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
        "is_favorited": bool(record[3]),
    }


class Sqlite:
    def __init__(self, db_filename):
        self.db_filename = db_filename
        logger.info("DB filename = %s", self.db_filename)

        self._create_tables_if_not_exists()
        self._migrate_db()

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
            "snippet text NOT NULL," \
            "is_favorited BOOLEAN NOT NULL" \
            ");"
        cursor.execute(cheatsheets_table)
        Sqlite._close(conn)

    def _migrate_db(self):
        """Migrate the DB tabke if needed.

        A 'is_favorited' column was added. This function checks
        if it's missing and creates it with 'false' values.
        """
        if self._does_column_exist("is_favorited"):
            return

        logger.info("'is_favorited' is missing - creating it")

        conn, cursor = self._connect()
        cursor.execute(f"ALTER TABLE {CHEATSHEETS_TABLE} ADD COLUMN is_favorited BOOLEAN")
        cursor.execute(f"UPDATE {CHEATSHEETS_TABLE} SET is_favorited=False;");
        Sqlite._close(conn)

    def _does_column_exist(self, column_name):
        conn, cursor = self._connect()

        column_exists = False

        cursor.execute(f"PRAGMA table_info({CHEATSHEETS_TABLE})")
        columns = cursor.fetchall()
        for column in columns:
            if column[1] == column_name:
                column_exists = True
                break

        Sqlite._close(conn)
        return column_exists

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

    def add_cheatsheet(self, snippet, section, is_favorited):
        conn, cursor = self._connect()
        try:
            cursor.execute(f"INSERT INTO {CHEATSHEETS_TABLE} (section, snippet, is_favorited) "
                           f"VALUES ('{sql_escape(section)}', "
                           f"'{sql_escape(snippet)}', "
                           f"{is_favorited});")
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

    def toggle_favorited(self, cheatsheet_id):
        cheatsheet = self.read_cheatsheet(cheatsheet_id)

        was_favorited = cheatsheet["is_favorited"]
        new_state = not was_favorited

        conn, cursor = self._connect()
        try:
            cursor.execute(f"UPDATE {CHEATSHEETS_TABLE} "
                           f"SET "
                           f"is_favorited={new_state} "
                           f"WHERE id={cheatsheet_id};")
            return new_state
        except Exception:
            return not new_state
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
