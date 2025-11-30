# data_manager

from models import parse_users
from .data import Data
import logging

def load_data():
    # load users
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