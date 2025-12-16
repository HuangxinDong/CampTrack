import logging
from persistence.db_context import DBContext


class UserManager:
    """SQLite-backed user persistence."""

    def __init__(self, db_context=None):
        self.db = db_context or DBContext()

    def read_all(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT username, password, role, enabled, daily_payment_rate FROM users")
            rows = cursor.fetchall()
            users = []
            for row in rows:
                user = {
                    "username": row[0],
                    "password": row[1],
                    "role": row[2],
                    "enabled": bool(row[3])
                }
                if row[4] is not None:
                    user["daily_payment_rate"] = row[4]
                users.append(user)
            return users
        except Exception as exc:
            logging.error(f"Error reading users: {exc}")
            return []
        finally:
            conn.close()

    def find_user(self, username):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT username, password, role, enabled, daily_payment_rate FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if not row:
                return None
            user = {
                "username": row[0],
                "password": row[1],
                "role": row[2],
                "enabled": bool(row[3])
            }
            if row[4] is not None:
                user["daily_payment_rate"] = row[4]
            return user
        except Exception as exc:
            logging.error(f"Error finding user: {exc}")
            return None
        finally:
            conn.close()

    def create_user(self, username, password, role, **kwargs):
        if not username or not username.strip():
            return False, "Username cannot be empty."
        if not role or not role.strip():
            return False, "Role cannot be empty."

        if self.find_user(username):
            return False, "Username already exists."

        daily_payment_rate = kwargs.get("daily_payment_rate")

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role, enabled, daily_payment_rate) VALUES (?, ?, ?, ?, ?)",
                (username, password, role, 1, daily_payment_rate)
            )
            conn.commit()
            return True, f"User {username} created successfully."
        except Exception as exc:
            logging.error(f"Error creating user: {exc}")
            return False, f"Error creating user: {exc}"
        finally:
            conn.close()

    def delete_user(self, username):
        if not self.find_user(username):
            return False, "User not found."

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            return True, f"User {username} deleted."
        except Exception as exc:
            logging.error(f"Error deleting user: {exc}")
            return False, f"Error deleting user: {exc}"
        finally:
            conn.close()

    def toggle_user_status(self, username, enabled):
        if not self.find_user(username):
            return False, "User not found."

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET enabled = ? WHERE username = ?", (1 if enabled else 0, username))
            conn.commit()
            state = "enabled" if enabled else "disabled"
            return True, f"User {username} status set to {state}."
        except Exception as exc:
            logging.error(f"Error updating user status: {exc}")
            return False, f"Error updating user status: {exc}"
        finally:
            conn.close()

    def update_password(self, username, new_password):
        if not self.find_user(username):
            return False, "User not found."

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
            conn.commit()
            return True, f"Password updated for {username}."
        except Exception as exc:
            logging.error(f"Error updating password: {exc}")
            return False, f"Error updating password: {exc}"
        finally:
            conn.close()

    def update_daily_payment_rate(self, username, new_daily_payment_rate):
        user = self.find_user(username)
        if user is None:
            return False, "User not found."
        if user["role"] != "Leader":
            return False, "User is not a leader"

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET daily_payment_rate = ? WHERE username = ?", (new_daily_payment_rate, username))
            conn.commit()
            return True, f"Payment rate updated for {username}."
        except Exception as exc:
            logging.error(f"Error updating payment rate: {exc}")
            return False, f"Error updating payment rate: {exc}"
        finally:
            conn.close()

    def update_username(self, old_username, new_username):
        if self.find_user(new_username):
            return False, "Username already exists."

        if not self.find_user(old_username):
            return False, "User not found."

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, old_username))
            conn.commit()
            return True, f"Username updated to {new_username}."
        except Exception as exc:
            logging.error(f"Error updating username: {exc}")
            return False, f"Error updating username: {exc}"
        finally:
            conn.close()

    def update_role(self, username, new_role):
        user = self.find_user(username)
        if user is None:
            return False, "User not found."

        match new_role.lower():
            case "leader" | "l":
                role_str = "Leader"
            case "coordinator" | "c":
                role_str = "Coordinator"
            case _:
                return False, "Invalid role."

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET role = ? WHERE username = ?", (role_str, username))
            if role_str == "Leader" and "daily_payment_rate" not in user:
                cursor.execute("UPDATE users SET daily_payment_rate = 0.0 WHERE username = ?", (username,))
            conn.commit()
            return True, f"Role updated to {role_str} for {username}."
        except Exception as exc:
            logging.error(f"Error updating role: {exc}")
            return False, f"Error updating role: {exc}"
        finally:
            conn.close()