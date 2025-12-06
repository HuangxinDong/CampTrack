import os
import json
import logging

from models.users.admin import Admin
from models.users.coordinator import Coordinator
from models.users.leader import Leader
from .data import Data

CLASS_MAP = {
    "Admin": Admin,
    "Leader": Leader,
    "Coordinator": Coordinator
}

class UserManager:
    def __init__(self, filepath="data/users.json"):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, "w") as f:
                f.write("{}")

    def _parse_users(self, json_str):
        user_objects = []

        if not json_str:
            logging.warning("Users file is empty")
            return []

        try:
            raw_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON: {e}")
            return []

        if raw_data is None or not isinstance(raw_data, dict):
            logging.error("JSON root is not a dictionary")
            return []

        for key, attributes in raw_data.items():
            role = attributes.get("role")
            target_class = CLASS_MAP.get(role)
            if target_class:
                try:
                    obj = target_class(**attributes)
                    user_objects.append(obj)
                except TypeError as e:
                    logging.error(f"Data mismatch for {key}: {e}")
            else:
                logging.warning(f"Unknown role '{role}' for user '{key}'")

        return user_objects

    def read_all(self):
        try:
            with open(self.filepath, "r") as file:
                json_content = file.read()
        except FileNotFoundError:
            logging.critical(f"Error: Could not find {self.filepath}")
            return []

        return self._parse_users(json_content)

    def save_data(self, data):
        if data.users:
            users_dict = {}
            for user in data.users:
                users_dict[user.username] = user.to_dict()
            
            try:
                with open(self.filepath, "w") as file:
                    json.dump(users_dict, file, indent=4)
            except Exception as e:
                logging.error(f"Error saving users: {e}")

    def load_data(self):
        try:
            with open(self.filepath, "r") as file:
                json_content = file.read()
            users = self._parse_users(json_content)

            if users is None:
                logging.error("Error: Users file exist but parsed into None.")
                return None
            
        except FileNotFoundError:
            logging.critical(f"Error: Could not find {self.filepath}")
            return None

        return Data(users)
