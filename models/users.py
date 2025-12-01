import json
import logging

class User:
    def __init__(self, username, password, role=None, enabled=True):
        self.username = username
        self.password = password
        self.role = role
        self.enabled = enabled

    def to_dict(self):
        """Base to_dict method, can be overridden by subclasses"""
        return {
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "enabled": self.enabled
        }

    def __repr__(self):
        return f"<{self.role}: {self.username}>"

class Admin(User):
    """
    Admin model class. Inherits from User.
    Represents an administrator with full system access.
    """
    def __init__(self, username, password, role="Admin", enabled=True):
        super().__init__(username, password, role, enabled)

class Leader(User):
    def __init__(self, username, password, role, enabled, daily_payment_rate):
        super().__init__(username, password, role, enabled)
        self.daily_payment_rate = daily_payment_rate

    def to_dict(self):
        data = super().to_dict()
        data['daily_payment_rate'] = self.daily_payment_rate
        return data

class Coordinator(User):
    pass

CLASS_MAP = {
    "Admin": Admin,
    "Leader": Leader,
    "Coordinator": Coordinator
}

def parse_users(json_str):
    user_objects = []

    if not json_str:
        logging.warning("Warning: Users file is empty.")
        return False, []
    
    try: 
        raw_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logging.error(f"Error: Failed to decode JSON. {e}")
        return False, []
    
    if raw_data is None or not isinstance(raw_data, dict):
        logging.error("Error: JSON root is not a dictionary.")
        return False, []
    
    for key, attributes in raw_data.items():
        role = attributes.get("role")
        if role in CLASS_MAP:
            target_class = CLASS_MAP[role]
            try:
                new_object = target_class(**attributes)
                user_objects.append(new_object)
            except TypeError as e:
                logging.error(f"Error: data mismatch for {key}: {e}")
        else:
            logging.warning(f"Warning: unable to deserialize user type '{role}' for key '{key}'.")
    return True, user_objects