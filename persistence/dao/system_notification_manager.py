import json
import os
from models.sys_notification import SystemNotification

class SystemNotificationManager:
    def __init__(self, filepath="persistence/data/system_notifications.json"):
        self.file_path = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def read_all(self):
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        if not isinstance(data, list):
            return []

        results = []
        for item in data:
            try:
                results.append(SystemNotification.from_dict(item))
            except Exception:
                continue
        return results

    def add(self, notification):
        notifications = self.read_all()
        notifications.append(notification)
        
        data = [n.to_dict() for n in notifications]
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def get_user_notifications(self, username):
        notifications = self.read_all()
        return [n for n in notifications if n.to_user == username]