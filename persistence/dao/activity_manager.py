import logging
from persistence.db_context import DBContext


class ActivityManager:
    """SQLite-backed activity library manager."""

    def __init__(self, db_context=None):
        self.db = db_context or DBContext()

    def load_library(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name, is_indoor FROM activity_library")
            rows = cursor.fetchall()
            return {row[0]: {"is_indoor": bool(row[1])} for row in rows}
        except Exception as exc:
            logging.error(f"Error loading activity library: {exc}")
            return {}
        finally:
            conn.close()

    def add_activity(self, name, is_indoor=False):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM activity_library WHERE name = ? COLLATE NOCASE", (name,))
            if cursor.fetchone():
                return False

            cursor.execute(
                "INSERT INTO activity_library (name, is_indoor) VALUES (?, ?)",
                (name, 1 if is_indoor else 0),
            )
            conn.commit()
            return True
        except Exception as exc:
            logging.error(f"Error adding activity: {exc}")
            return False
        finally:
            conn.close()

    def save_library(self, activities):
        """Replace entire library with provided dict (used sparingly)."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM activity_library")
            for name, meta in activities.items():
                cursor.execute(
                    "INSERT INTO activity_library (name, is_indoor) VALUES (?, ?)",
                    (name, 1 if meta.get("is_indoor") else 0),
                )
            conn.commit()
        except Exception as exc:
            logging.error(f"Error saving activity library: {exc}")
        finally:
            conn.close()