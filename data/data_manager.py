# data_manager

from models import parse_users
from .data import Data
import logging
import json

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