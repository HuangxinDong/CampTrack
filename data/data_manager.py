from models.users.admin import Admin
from models.users.coordinator import Coordinator
from models.users.leader import Leader
from .data import Data
import logging
import json

CLASS_MAP = {
    "Admin": Admin,
    "Leader": Leader,
    "Coordinator": Coordinator
}

def parse_users(json_str):
    user_objects = []

    if not json_str:
        logging.warning("Users file is empty")
        return False, []

    try:
        raw_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON: {e}")
        return False, []

    if raw_data is None or not isinstance(raw_data, dict):
        logging.error("JSON root is not a dictionary")
        return False, []

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

    return True, user_objects

def save_data(data):
    """
    Save data to JSON files.
    """
    # Save users
    if data.users:
        users_dict = {}
        for user in data.users:
            users_dict[user.username] = user.to_dict()
        
        try:
            with open("data/users.json", "w") as file:
                json.dump(users_dict, file, indent=4)
        except Exception as e:
            logging.error(f"Error saving users: {e}")

def load_data():
    """
    load data from JSON files.
    """
    # Load users
    try:
        with open("data/users.json", "r") as file:
            json_content = file.read()
        validated, users = parse_users(json_content)
        if not validated:
            return None

        if users is None:
            logging.error("Error: Users file exist but parsed into None.")
            return None
        
    except FileNotFoundError:
        logging.critical("Error: Could not find data/users.json")
        return None
    
    # Load additional data (once created)

    return Data(users)