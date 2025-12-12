from typing import List, Dict, Any, Tuple, Optional
from persistence.dao.activity_manager import ActivityManager
from persistence.dao.camp_manager import CampManager
from models.activity import Activity, Session

class ActivityService:
    def __init__(self, activity_manager: ActivityManager, camp_manager: CampManager):
        self.activity_manager = activity_manager
        self.camp_manager = camp_manager

    def get_library(self) -> Dict[str, Dict[str, Any]]:
        return self.activity_manager.load_library()

    def search_library(self, query: str) -> List[str]:
        library = self.get_library()
        if not library:
            return []
        return [name for name in library.keys() if query.lower() in name.lower()]

    def add_to_library(self, name: str, is_indoor: bool) -> Tuple[bool, str]:
        if not name.strip():
            return False, "Activity name cannot be empty."
        
        library = self.get_library()
        if name in library:
            return False, f"Activity '{name}' already exists in library."

        self.activity_manager.add_activity_type(name, is_indoor)
        return True, f"Activity '{name}' added to library."

    def schedule_activity(self, camp_name: str, activity_name: str, date_str: str, session_name: str, force_replace: bool = False) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Schedules an activity for a camp.
        Returns (success, message, conflict_activity_data).
        If conflict exists and force_replace is False, returns conflict data.
        """
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found.", None

        library = self.get_library()
        if activity_name not in library:
            return False, f"Activity '{activity_name}' not found in library.", None

        is_indoor = library[activity_name].get("is_indoor", False)

        # Validation: Max occurrences per day
        daily_count = 0
        for act in camp.activities:
            a_date = act.get("date")
            a_name = act.get("name")
            if a_date == date_str and a_name == activity_name:
                daily_count += 1
        
        if daily_count >= 2:
             return False, f"Limit reached: '{activity_name}' is already scheduled {daily_count} times on {date_str}. (Max 2)", None

        # Check for conflicts
        conflict_index = -1
        conflict_activity = None
        
        for i, existing_activity in enumerate(camp.activities):
            ex_date = existing_activity.get("date")
            ex_session = existing_activity.get("session")

            if ex_date == date_str and ex_session == session_name:
                conflict_activity = existing_activity
                conflict_index = i
                break

        if conflict_activity:
            if not force_replace:
                return False, "Time slot conflict detected.", conflict_activity
            else:
                # Remove existing
                camp.activities.pop(conflict_index)

        # Create and Add
        try:
            session_enum = Session[session_name]
            activity = Activity(activity_name, date_str, session_enum, is_indoor=is_indoor)
            camp.activities.append(activity.to_dict())
            self.camp_manager.update(camp)
            return True, f"Successfully scheduled '{activity_name}' for {date_str} ({session_name}).", None
        except KeyError:
            return False, f"Invalid session name: {session_name}", None

    def remove_activity(self, camp_name: str, activity_index: int) -> Tuple[bool, str]:
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found."

        if not (0 <= activity_index < len(camp.activities)):
            return False, "Invalid activity index."

        removed = camp.activities.pop(activity_index)
        self.camp_manager.update(camp)
        return True, f"Activity '{removed.get('name')}' removed."

    def add_camper_to_activity(self, camp_name: str, activity_index: int, camper_name: str) -> Tuple[bool, str]:
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found."

        if not (0 <= activity_index < len(camp.activities)):
            return False, "Invalid activity index."

        activity = camp.activities[activity_index]
        current_ids = activity.get('camper_ids', [])
        
        if camper_name in current_ids:
            return False, f"Camper '{camper_name}' is already in this activity."

        # Verify camper belongs to camp
        if not any(c.name == camper_name for c in camp.campers):
             return False, f"Camper '{camper_name}' is not in this camp."

        activity['camper_ids'].append(camper_name)
        self.camp_manager.update(camp)
        return True, f"Added {camper_name} to activity."

    def remove_camper_from_activity(self, camp_name: str, activity_index: int, camper_name: str) -> Tuple[bool, str]:
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found."

        if not (0 <= activity_index < len(camp.activities)):
            return False, "Invalid activity index."

        activity = camp.activities[activity_index]
        current_ids = activity.get('camper_ids', [])
        
        if camper_name not in current_ids:
            return False, f"Camper '{camper_name}' is not in this activity."

        current_ids.remove(camper_name)
        self.camp_manager.update(camp)
        return True, f"Removed {camper_name} from activity."

    def add_all_campers_to_activity(self, camp_name: str, activity_index: int) -> Tuple[bool, str]:
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found."

        if not (0 <= activity_index < len(camp.activities)):
            return False, "Invalid activity index."

        activity = camp.activities[activity_index]
        current_ids = set(activity.get('camper_ids', []))
        added_count = 0
        
        for camper in camp.campers:
            if camper.name not in current_ids:
                activity['camper_ids'].append(camper.name)
                added_count += 1
        
        if added_count > 0:
            self.camp_manager.update(camp)
            return True, f"Added {added_count} campers to '{activity['name']}'."
        else:
            return False, "All campers are already in this activity."
