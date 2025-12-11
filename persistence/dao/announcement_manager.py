import json
import os
import logging

class AnnouncementManager:
    def __init__(self, data_file='persistence/data/announcements.json'):
        self.data_file = data_file
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump([], f)

    def read_all(self):
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def add(self, announcement_data):
        announcements = self.read_all()
        announcements.append(announcement_data)
        
        try:
            with open(self.data_file, 'w') as f:
                json.dump(announcements, f, indent=4)
        except Exception as e:
            logging.error(f"Error adding announcement: {e}")
            raise

    def get_latest(self):
        announcements = self.read_all()
        if not announcements:
            return None
        # Sort by created_at descending
        announcements.sort(key=lambda x: x['created_at'], reverse=True)
        return announcements[0]
