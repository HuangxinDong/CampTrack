import os
import sys

CURRENT_DIR = os.path.dirname(__file__)          
PROJECT_ROOT = os.path.dirname(CURRENT_DIR) 

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.users.leader import LeaderManager

if __name__ == "__main__":
    camp_id = "48ee70b4-679f-4379-9ab0-dd9295c38016" 
    csv_path = csv_path = os.path.join(PROJECT_ROOT,"persistence","data","campers.csv")
    manager = LeaderManager()
    manager.assign_campers_from_csv(camp_id, csv_path)
    



