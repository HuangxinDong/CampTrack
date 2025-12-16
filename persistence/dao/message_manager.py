import logging
from collections import defaultdict
from persistence.db_context import DBContext


class MessageManager:
    """SQLite-backed message persistence."""

    def __init__(self, db_context=None):
        self.db = db_context or DBContext()

    def read_all(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT message_id, from_user, to_user, content, sent_at, mark_as_read FROM messages"
            )
            rows = cursor.fetchall()
            return [
                {
                    "message_id": row[0],
                    "from_user": row[1],
                    "to_user": row[2],
                    "content": row[3],
                    "sent_at": row[4],
                    "mark_as_read": bool(row[5]),
                }
                for row in rows
            ]
        except Exception as exc:
            logging.error(f"Error reading messages: {exc}")
            return []
        finally:
            conn.close()

    def add(self, message):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO messages (message_id, from_user, to_user, content, sent_at, mark_as_read)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message.get("message_id"),
                    message.get("from_user"),
                    message.get("to_user"),
                    message.get("content"),
                    message.get("sent_at"),
                    1 if message.get("mark_as_read") else 0,
                ),
            )
            conn.commit()
        except Exception as exc:
            logging.error(f"Error adding message: {exc}")
            raise
        finally:
            conn.close()

    def update(self, updated_message):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE messages
                SET from_user=?, to_user=?, content=?, sent_at=?, mark_as_read=?
                WHERE message_id=?
                """,
                (
                    updated_message.get("from_user"),
                    updated_message.get("to_user"),
                    updated_message.get("content"),
                    updated_message.get("sent_at"),
                    1 if updated_message.get("mark_as_read") else 0,
                    updated_message.get("message_id"),
                ),
            )
            if cursor.rowcount == 0:
                self.add(updated_message)
            else:
                conn.commit()
        except Exception as exc:
            logging.error(f"Error updating message: {exc}")
            raise
        finally:
            conn.close()

    def mark_as_read_batch(self, message_ids: list):
        if not message_ids:
            return

        placeholders = ",".join(["?"] * len(message_ids))
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"UPDATE messages SET mark_as_read = 1 WHERE message_id IN ({placeholders})",
                message_ids,
            )
            conn.commit()
        except Exception as exc:
            logging.error(f"Error marking messages as read: {exc}")
            raise
        finally:
            conn.close()

    def get_unread_message_count(self, username: str) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM messages WHERE to_user = ? AND mark_as_read = 0",
                (username,),
            )
            row = cursor.fetchone()
            return row[0] if row else 0
        except Exception as exc:
            logging.error(f"Error counting unread messages: {exc}")
            return 0
        finally:
            conn.close()

    def get_conversation_summaries(self, username: str) -> list:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT message_id, from_user, to_user, content, sent_at, mark_as_read
                FROM messages
                WHERE from_user = ? OR to_user = ?
                ORDER BY sent_at ASC
                """,
                (username, username),
            )
            rows = cursor.fetchall()
            messages = [
                {
                    "message_id": row[0],
                    "from_user": row[1],
                    "to_user": row[2],
                    "content": row[3],
                    "sent_at": row[4],
                    "mark_as_read": bool(row[5]),
                }
                for row in rows
            ]
        except Exception as exc:
            logging.error(f"Error loading conversations: {exc}")
            return []
        finally:
            conn.close()

        conversations = self._get_conversations_from_messages(messages, username)
        summaries = []
        for partner, conv_messages in conversations.items():
            last_message = self._get_last_message(conv_messages)
            summaries.append(
                {
                    "partner": partner,
                    "unread_count": self._count_unread_messages_in_list(conv_messages, username),
                    "last_message": last_message,
                    "preview": self._truncate_last_message(last_message["content"]) if last_message else "",
                }
            )

        summaries.sort(
            key=lambda summary: summary["last_message"]["sent_at"] if summary["last_message"] else "",
            reverse=True,
        )
        return summaries

    def _get_conversations_from_messages(self, messages, username):
        conversations = defaultdict(list)
        for msg in messages:
            if msg["from_user"] == username:
                conversations[msg["to_user"]].append(msg)
            elif msg["to_user"] == username:
                conversations[msg["from_user"]].append(msg)
        return conversations

    def _count_unread_messages_in_list(self, messages: list, username: str) -> int:
        return sum(1 for m in messages if m["to_user"] == username and not m.get("mark_as_read", False))

    def _get_last_message(self, messages: list):
        if not messages:
            return None
        return max(messages, key=lambda m: m["sent_at"])

    def _truncate_last_message(self, content: str, max_length: int = 30) -> str:
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."


