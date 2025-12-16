import logging
from persistence.db_context import DBContext


class AnnouncementManager:
    """SQLite-backed announcements."""

    def __init__(self, db_context=None):
        self.db = db_context or DBContext()

    def read_all(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT announcement_id, author, content, created_at FROM announcements")
            rows = cursor.fetchall()
            return [
                {
                    "announcement_id": row[0],
                    "author": row[1],
                    "content": row[2],
                    "created_at": row[3],
                }
                for row in rows
            ]
        except Exception as exc:
            logging.error(f"Error reading announcements: {exc}")
            return []
        finally:
            conn.close()

    def add(self, announcement_data):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO announcements (announcement_id, author, content, created_at) VALUES (?, ?, ?, ?)",
                (
                    announcement_data.get("announcement_id"),
                    announcement_data.get("author"),
                    announcement_data.get("content"),
                    announcement_data.get("created_at"),
                ),
            )
            conn.commit()
        except Exception as exc:
            logging.error(f"Error adding announcement: {exc}")
            raise
        finally:
            conn.close()

    def get_latest(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT announcement_id, author, content, created_at FROM announcements ORDER BY created_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "announcement_id": row[0],
                "author": row[1],
                "content": row[2],
                "created_at": row[3],
            }
        except Exception as exc:
            logging.error(f"Error getting latest announcement: {exc}")
            return None
        finally:
            conn.close()
