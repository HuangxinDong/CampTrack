import os
import json
import logging
from datetime import datetime

class AuditLogManager:
    """Manages system audit logs."""

    def __init__(self, filepath="persistence/data/audit_logs.json"):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, "w") as f:
                f.write("[]")

    def _read_data(self):
        try:
            with open(self.filepath, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_data(self, data):
        try:
            with open(self.filepath, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving audit logs: {e}")

    def log_event(self, username, action, details=""):
        """
        Logs a system event.
        
        Args:
            username (str): The user performing the action.
            action (str): Short description of the action (e.g., "Create User").
            details (str): Additional info.
        """
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "username": username,
            "action": action,
            "details": details
        }
        
        logs = self._read_data()
        logs.append(entry)
        self._save_data(logs)

    def read_all(self):
        return self._read_data()

    def get_logs_by_user(self, username):
        logs = self._read_data()
        return [log for log in logs if log['username'] == username]
