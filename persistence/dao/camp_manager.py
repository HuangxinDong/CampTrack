from models.camp import Camp
import json
import logging
import os

class CampManager:
    def __init__(self, filepath="persistence/data/camps.json"):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, "w") as f:
                f.write("[]")

    def read_all(self):
        with open(self.filepath, "r") as f:
            try:
                data = json.load(f)
            except Exception as e:
                logging.error(f"Error reading camps.json: {e}")
                raise

        if not isinstance(data, list):
            raise ValueError("camps.json must contain a JSON array.")

        try:
            valid_camps = []
            for item in data:
                try:
                    if not isinstance(item, dict):
                        logging.warning(f"Skipping invalid item in camps.json (not a dict): {item}")
                        continue
                    valid_camps.append(Camp.from_dict(item))
                except Exception as e:
                    logging.warning(f"Skipping undefined/malformed camp item: {e}")
            
            return valid_camps
        except Exception as e:
            logging.error(f"Error converting JSON to Camp objects: {e}")
            raise

    def add(self, camp: Camp):
        camps = self.read_all()
        camps.append(camp)
        data = [c.to_dict() for c in camps]

        try:
            with open(self.filepath, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logging.error(f"Error writing camps.json: {e}")
            raise


    def update(self, updatedCamp: Camp):
        camps = self.read_all()
        updated = False

        for i, camp in enumerate(camps):
            if camp.camp_id == updatedCamp.camp_id:
                camps[i] = updatedCamp
                updated = True
                break

        if not updated:
            camps.append(updatedCamp)

        data = [c.to_dict() for c in camps]
        try:
            with open(self.filepath, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logging.error(f"Error writing camps.json: {e}")
            raise  
    
    #this is added by Yufei to import csv for leaders
    def get_camp_by_id(self, camp_id):
        camps = self.read_all()
        for camp in camps:
            if camp.camp_id == camp_id:
                return camp
        return None


