import csv
import os
import logging
from models.camper import Camper
from models.camp import Camp

class CamperManager:
    """
    Manages camper-related operations, primarily CSV importing.
    """
    DEF_PATH = os.path.join("persistence", "data", "campers")

    def __init__(self):
        if not os.path.exists(self.DEF_PATH):
            os.makedirs(self.DEF_PATH, exist_ok=True)

    def get_available_csv_files(self):
        """Returns a list of .csv filenames available for import."""
        if not os.path.exists(self.DEF_PATH):
            return []
        return [f for f in os.listdir(self.DEF_PATH) if f.endswith(".csv")]

    def import_campers_from_csv(self, camp, filename, context):
        """
        Imports campers from a CSV file into the given camp.
        
        Args:
            camp (Camp): The target camp object.
            filename (str): Name of the file (e.g. "campers.csv").
            context (AppContext): For accessing camp_manager to read other camps for validation.

        Returns:
            dict: {
                "imported_count": int,
                "skipped_count": int,
                "errors": list[str],
                "warnings": list[str]
            }
        """
        results = {
            "imported_count": 0,
            "skipped_count": 0,
            "errors": [],
            "warnings": []
        }
        
        csv_path = os.path.join(self.DEF_PATH, filename)

        # Identify conflicting camps
        all_camps = context.camp_manager.read_all()
        conflicting_camps = []
        for other_camp in all_camps:
            if other_camp.camp_id == camp.camp_id:
                continue
            if Camp.dates_overlap(camp.start_date, camp.end_date, other_camp.start_date, other_camp.end_date):
                conflicting_camps.append(other_camp)

        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    name = row.get("name")
                    if not name:
                        continue

                    # Check if already in current camp
                    if any(c.name.lower() == name.lower() for c in camp.campers):
                        results["warnings"].append(f"Skipping '{name}': Already registered in this camp.")
                        results["skipped_count"] += 1
                        continue
                        
                    # Check overlapping camps
                    conflict_found = False
                    for other_camp in conflicting_camps:
                        if any(c.name.lower() == name.lower() for c in other_camp.campers):
                            results["warnings"].append(f"Skipping '{name}': Already registered in overlapping camp '{other_camp.name}'.")
                            conflict_found = True
                            break
                    
                    if conflict_found:
                        results["skipped_count"] += 1
                        continue

                    # Create Camper
                    age_raw = row.get("age")
                    age = int(age_raw) if age_raw and age_raw.isdigit() else 0

                    new_camper = Camper(
                        name=name,
                        age=age,
                        contact=row.get("contact") or "",
                        medical_info=row.get("medical_info") or ""
                    )
                    camp.campers.append(new_camper)
                    results["imported_count"] += 1
            
            # Persist changes
            if results["imported_count"] > 0:
                context.camp_manager.update(camp)

        except Exception as e:
            results["errors"].append(f"CSV Error: {str(e)}")
            logging.error(f"Error importing campers CSV: {e}")

        return results

    def import_roster_to_activity(self, activity_data, filename, camp):
        """
        Imports a list of camper names from CSV and assigns them to the activity.
        Must match existing campers in the camp.
        """
        results = {
            "imported_count": 0,
            "skipped_count": 0,
            "errors": [],
            "warnings": []
        }
        
        csv_path = os.path.join(self.DEF_PATH, filename)
        
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                # Check for 'name' column
                if reader.fieldnames and 'name' not in reader.fieldnames:
                     results["errors"].append("CSV missing 'name' column header.")
                     return results

                current_roster = set(activity_data.get('camper_ids', []))
                
                for row in reader:
                    name = row.get("name")
                    if not name: continue
                    
                    # 1. Find camper in Camp
                    camper_obj = next((c for c in camp.campers if c.name.lower() == name.lower()), None)
                    
                    if not camper_obj:
                        results["warnings"].append(f"Skipped '{name}': Not found in this camp.")
                        results["skipped_count"] += 1
                        continue
                        
                    # 2. Check if already in Activity
                    if camper_obj.name in current_roster:
                        results["skipped_count"] += 1
                        continue
                        
                    # 3. Add to Activity
                    activity_data['camper_ids'].append(camper_obj.name)
                    current_roster.add(camper_obj.name)
                    results["imported_count"] += 1
                    
        except Exception as e:
             results["errors"].append(f"CSV Error: {str(e)}")
             logging.error(f"Error importing roster: {e}")
             
        return results
