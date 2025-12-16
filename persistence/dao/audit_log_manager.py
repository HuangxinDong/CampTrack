import logging
from datetime import datetime
from persistence.db_context import DBContext


class AuditLogManager:
    """SQLite-backed audit logging."""

    def __init__(self, db_context=None):
        self.db = db_context or DBContext()

    def log_event(self, username, action, details=""):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO audit_logs (timestamp, username, action, details) VALUES (?, ?, ?, ?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username, action, details),
            )
            conn.commit()
        except Exception as exc:
            logging.error(f"Error logging event: {exc}")
        finally:
            conn.close()

    def read_all(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT log_id, timestamp, username, action, details FROM audit_logs ORDER BY log_id DESC")
            rows = cursor.fetchall()
            return [
                {
                    "log_id": row[0],
                    "timestamp": row[1],
                    "username": row[2],
                    "action": row[3],
                    "details": row[4],
                }
                for row in rows
            ]
        except Exception as exc:
            logging.error(f"Error reading audit logs: {exc}")
            return []
        finally:
            conn.close()

    def get_logs_by_user(self, username):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT log_id, timestamp, username, action, details FROM audit_logs WHERE username = ? ORDER BY log_id DESC",
                (username,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "log_id": row[0],
                    "timestamp": row[1],
                    "username": row[2],
                    "action": row[3],
                    "details": row[4],
                }
                for row in rows
            ]
        except Exception as exc:
            logging.error(f"Error reading audit logs for {username}: {exc}")
            return []
        finally:
            conn.close()
