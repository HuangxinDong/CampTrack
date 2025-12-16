import logging
from models.sys_notification import SystemNotification
from persistence.db_context import DBContext


class SystemNotificationManager:
    """SQLite-backed system notifications."""

    def __init__(self, db_context=None):
        self.db = db_context or DBContext()

    def read_all(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT sys_notification_id, to_user, type, content, created_at FROM system_notifications"
            )
            rows = cursor.fetchall()
            return [
                SystemNotification.from_dict(
                    {
                        "sys_notification_id": row[0],
                        "to_user": row[1],
                        "type": row[2],
                        "content": row[3],
                        "created_at": row[4],
                    }
                )
                for row in rows
            ]
        except Exception as exc:
            logging.error(f"Error reading system notifications: {exc}")
            return []
        finally:
            conn.close()

    def add(self, notification: SystemNotification):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            payload = notification.to_dict()
            cursor.execute(
                "INSERT INTO system_notifications (sys_notification_id, to_user, type, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    payload["sys_notification_id"],
                    payload["to_user"],
                    payload["type"],
                    payload["content"],
                    payload["created_at"],
                ),
            )
            conn.commit()
        except Exception as exc:
            logging.error(f"Error adding system notification: {exc}")
            raise
        finally:
            conn.close()

    def get_user_notifications(self, username):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT sys_notification_id, to_user, type, content, created_at FROM system_notifications WHERE to_user = ?",
                (username,),
            )
            rows = cursor.fetchall()
            return [
                SystemNotification.from_dict(
                    {
                        "sys_notification_id": row[0],
                        "to_user": row[1],
                        "type": row[2],
                        "content": row[3],
                        "created_at": row[4],
                    }
                )
                for row in rows
            ]
        except Exception as exc:
            logging.error(f"Error reading notifications for user {username}: {exc}")
            return []
        finally:
            conn.close()