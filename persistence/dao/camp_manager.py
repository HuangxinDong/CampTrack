import pandas as pd
import numpy as np
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

    def get_camps_by_leader(self, leader_username: str) -> list:
        """
        Get all camps assigned to a specific leader.

        Args:
            leader_username: The username of the leader

        Returns:
            list[Camp]: Camps where camp_leader matches username
        """
        camps = self.read_all()
        return [camp for camp in camps if camp.camp_leader == leader_username]

    def get_global_activity_engagement(self) -> dict:
        """
        Calculates the GLOBAL percentage of unique campers participating in each activity type,
        aggregated across ALL camps using Pandas.
        
        Returns:
            dict: {"Archery": 0.5, "Swimming": 0.75} (Values 0.0 to 1.0)
        """
        camps = self.read_all()
        
        # 1. Total Unique Campers in Organization
        global_unique_campers = set()
        activity_data = [] # List of {'activity': name, 'camper': id/name}

        for c in camps:
            # Collect all campers in this camp
            if hasattr(c, 'campers'):
                for camper in c.campers:
                     global_unique_campers.add(camper.name)

            # Collect activity participation data
            activities = getattr(c, "activities", [])
            for act in activities:
                # Handle both dict and object access safely
                name = act.get("name") if isinstance(act, dict) else getattr(act, 'name', 'Unknown')
                ids = act.get("camper_ids", []) if isinstance(act, dict) else getattr(act, 'camper_ids', [])
                
                for camper_id in ids:
                     activity_data.append({'activity': name, 'camper': camper_id})
        
        total_unique = len(global_unique_campers)
        if total_unique == 0:
            return {}

        if not activity_data:
             return {}

        # 2. Pandas Logic
        try:
            df = pd.DataFrame(activity_data)
            
            # Group by activity and count unique campers
            # This handles the complex querying requirement efficiently
            engagement_series = df.groupby('activity')['camper'].nunique()
            
            # Calculate percentages
            metrics = (engagement_series / total_unique).round(2).to_dict()
            
            return metrics
            
        except ImportError:
            logging.error("Pandas not installed, falling back to basic calculation is recommended but Pandas was requested.")
            return {}
        except Exception as e:
            logging.error(f"Error in pandas engagement calculation: {e}")
            return {}

    def get_camp_overview_stats(self) -> dict:
        """
        Calculates System-Wide Aggregates and Detailed Camp Status using Pandas & Numpy.
        
        Returns:
            dict: { 
                'aggregates': { 'total_campers': int, ... },
                'details': [ {'name': 'Camp A', 'status': 'Good', ...} ]
            }
        """
        camps = self.read_all()
        if not camps:
            return {'aggregates': {}, 'details': []}

        # 1. Build Data List
        data = []
        for c in camps:
            leader = c.camp_leader if c.camp_leader else None
            stock = getattr(c, 'current_food_stock', 0)
            count = len(getattr(c, 'campers', []))
            
            data.append({
                'name': c.name,
                'leader': leader,
                'campers_count': count,
                'food_stock': stock,
                'schedule_status': c.get_schedule_status(),
                'is_shortage': c.is_food_shortage()
            })

        # 2. Create DataFrame
        try:
            df = pd.DataFrame(data)

            # 3. Calculate Aggregates (System Summary)
            aggregates = {
                'total_campers': int(df['campers_count'].sum()),
                'total_food': int(df['food_stock'].sum()),
                'assigned_leaders': int(df['leader'].notna().sum()),
                'total_camps': len(df),
                'shortage_camps': int(df['is_shortage'].sum())
            }

            # 4. Vectorized Status Logic using Numpy
            # Priority: Need Leader > Low Food > Good
            conditions = [
                pd.isna(df['leader']) | (df['leader'] == ''),
                df['is_shortage']
            ]
            choices = ['Need Leader', 'Low Food']
            
            df['status'] = np.select(conditions, choices, default='Good')

            # Handle None in leader column for display
            df['leader'] = df['leader'].fillna('[Unassigned]')

            return {
                'aggregates': aggregates,
                'details': df.to_dict('records')
            }

        except ImportError:
            logging.error("Pandas/Numpy not installed.")
            return {}
        except Exception as e:
            logging.error(f"Error in pandas overview calculation: {e}")
            return {}


