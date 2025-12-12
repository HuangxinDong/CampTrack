import json
import os
from cli.console_manager import console_manager

class ActivityManager:
    """
    Manages the persistence of the Activity Library (list of available activity names).
    """
    def __init__(self, filepath="persistence/data/activities.json"):
        self.file_path = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def load_library(self):
        """Returns the activity library (dictionary of name -> metadata). Migrates from list if needed."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    data = json.load(f)
                    
                # Migration: Convert old list format to new dict format
                if isinstance(data, list):
                    new_data = {name: {"is_indoor": False} for name in data}
                    self.save_library(new_data)
                    return new_data
                    
                return data
            except json.JSONDecodeError:
                return {}
        return {}

    def save_library(self, activities):
        """Saves the activity library dictionary to the file."""
        with open(self.file_path, "w") as f:
            json.dump(activities, f, indent=4)

    def add_activity(self, name, is_indoor=False):
        """Adds a new activity to the library."""
        library = self.load_library()
        
        # Case-insensitive check
        existing_names_lower = {k.lower() for k in library.keys()}
        if name.lower() in existing_names_lower:
            return False 
        
        library[name] = {"is_indoor": is_indoor}
        self.save_library(library)
        return True