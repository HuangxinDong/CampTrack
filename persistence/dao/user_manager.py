import os
import json
import logging

class UserManager:
    """All functions related to users data."""

    def __init__(self, filepath="persistence/data/users.json"):
        self.filepath = filepath
        self._ensure_file()
        self.users = self.read_all()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, "w") as f:
                f.write("[]")

    def _parse_users(self, json_str):
        try:
            raw_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON: {e}")
            return []

        if not isinstance(raw_data, list):
            logging.error("JSON root is not a list")
            return []

        return raw_data

    def read_all(self):
        try:
            with open(self.filepath, "r") as f:
                content = f.read()
        except FileNotFoundError:
            logging.critical(f"File not found: {self.filepath}")
            return []

        return self._parse_users(content)

    def save_data(self):
        users_list = self.users
        try:
            with open(self.filepath, "w") as f:
                json.dump(users_list, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving users: {e}")

    def find_user(self, username):
        for u in self.users:
            if u.get("username") == username:
                return u
        return None

    def create_user(self, username, password, role, **kwargs):
        if not username or not username.strip():
            return False, "Username cannot be empty."
        if not role or not role.strip():
            return False, "Role cannot be empty."

        if self.find_user(username):
            return False, "Username already exists."

        user = {
            "username": username,
            "password": password,
            "role": role,
            "enabled": True
        }
        user.update(kwargs)

        self.users.append(user)
        self.save_data()
        return True, f"User {username} created successfully."

    def delete_user(self, username):
        user = self.find_user(username)
        if user is None:
            return False, "User not found."
        self.users.remove(user)
        self.save_data()
        return True, f"User {username} deleted."

    def toggle_user_status(self, username, enabled):
        user = self.find_user(username)
        if user is None:
            return False, "User not found."
        user["enabled"] = enabled
        self.save_data()
        return True, f"User {username} status set to {'enabled' if enabled else 'disabled'}."

    def update_password(self, username, new_password):
        user = self.find_user(username)
        if user is None:
            return False, "User not found."
        user["password"] = new_password
        self.save_data()
        return True, f"Password updated for {username}."
        

    def update_daily_payment_rate(self, username, new_daily_payment_rate):
        user = self.find_user(username)
        if user is None:
            return False, "User not found."
        if user['role'] != 'Leader':
            return False, "User is not a leader"
        user["daily_payment_rate"] = new_daily_payment_rate
        self.save_data()
        return True, f"Payment rate updated for {username}."

    def update_username(self, old_username, new_username):
        if self.find_user(new_username):
            return False, "Username already exists."
        
        user = self.find_user(old_username)
        if user is None:
            return False, "User not found."
            
        user["username"] = new_username
        self.save_data()
        return True, f"Username updated to {new_username}."

    def update_role(self, username, new_role):
        user = self.find_user(username)
        if user is None:
            return False, "User not found."
            
        if new_role not in ["Leader", "Coordinator", "Admin"]:
             return False, "Invalid role."

        user["role"] = new_role
        # If switching to Leader, ensure daily_payment_rate exists
        if new_role == "Leader" and "daily_payment_rate" not in user:
            user["daily_payment_rate"] = 0.0
            
        self.save_data()
        return True, f"Role updated to {new_role} for {username}."