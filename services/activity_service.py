from typing import List, Dict, Any, Tuple, Optional
from persistence.dao.activity_manager import ActivityManager
from persistence.dao.camp_manager import CampManager
from models.activity import Activity, Session

class ActivityService:
    def __init__(self, activity_manager: ActivityManager, camp_manager: CampManager):
        self.activity_manager = activity_manager
        self.camp_manager = camp_manager

    def _normalize_activity(self, act: Any) -> Activity:
        """Ensure an Activity instance (tolerates legacy dict entries)."""
        if isinstance(act, Activity):
            return act
        return Activity.from_dict(act)

    def _normalize_activity_list(self, activities: List[Any]) -> List[Activity]:
        return [self._normalize_activity(a) for a in activities]

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

        created = self.activity_manager.add_activity(name, is_indoor)
        if not created:
            return False, f"Activity '{name}' already exists in library."
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

        camp.activities = self._normalize_activity_list(camp.activities)

        # Validation: Max occurrences per day (limit 2 per activity name per date)
        daily_count = 0
        for act in camp.activities:
            if str(act.date) == date_str and act.name == activity_name:
                daily_count += 1

        if daily_count >= 2:
            return False, f"Limit reached: '{activity_name}' is already scheduled {daily_count} times on {date_str}. (Max 2)", None

        # Check for conflicts in same slot
        conflict_index = -1
        conflict_activity: Optional[Activity] = None

        for i, existing_activity in enumerate(camp.activities):
            if str(existing_activity.date) == date_str and existing_activity.session.name == session_name:
                conflict_activity = existing_activity
                conflict_index = i
                break

        if conflict_activity:
            if not force_replace:
                return False, "Time slot conflict detected.", conflict_activity.to_dict()
            camp.activities.pop(conflict_index)

        # Create and Add
        try:
            session_enum = Session[session_name]
        except KeyError:
            return False, f"Invalid session name: {session_name}", None

        activity = Activity(activity_name, date_str, session_enum, is_indoor=is_indoor)
        camp.activities.append(activity)
        self.camp_manager.update(camp)
        return True, f"Successfully scheduled '{activity_name}' for {date_str} ({session_name}).", None

    def remove_activity(self, camp_name: str, activity_index: int) -> Tuple[bool, str]:
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found."

        camp.activities = self._normalize_activity_list(camp.activities)

        if not (0 <= activity_index < len(camp.activities)):
            return False, "Invalid activity index."

        removed = camp.activities.pop(activity_index)
        self.camp_manager.update(camp)
        return True, f"Activity '{removed.name}' removed."

    def add_camper_to_activity(self, camp_name: str, activity_index: int, camper_identifier: str) -> Tuple[bool, str]:
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found."

        camp.activities = self._normalize_activity_list(camp.activities)

        if not (0 <= activity_index < len(camp.activities)):
            return False, "Invalid activity index."

        activity = camp.activities[activity_index]

        camper = next((c for c in camp.campers if c.camper_id == camper_identifier or c.name == camper_identifier), None)
        if not camper:
            return False, f"Camper '{camper_identifier}' is not in this camp."

        if camper.camper_id in activity.campers:
            return False, f"Camper '{camper.name}' is already in this activity."

        activity.campers.append(camper.camper_id)
        self.camp_manager.update(camp)
        return True, f"Added {camper.name} to activity."

    def remove_camper_from_activity(self, camp_name: str, activity_index: int, camper_identifier: str) -> Tuple[bool, str]:
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found."

        camp.activities = self._normalize_activity_list(camp.activities)

        if not (0 <= activity_index < len(camp.activities)):
            return False, "Invalid activity index."

        activity = camp.activities[activity_index]
        camper = next((c for c in camp.campers if c.camper_id == camper_identifier or c.name == camper_identifier), None)
        if not camper:
            return False, f"Camper '{camper_identifier}' is not in this camp."

        if camper.camper_id not in activity.campers:
            return False, f"Camper '{camper.name}' is not in this activity."

        activity.campers = [cid for cid in activity.campers if cid != camper.camper_id]
        self.camp_manager.update(camp)
        return True, f"Removed {camper.name} from activity."

    def add_all_campers_to_activity(self, camp_name: str, activity_index: int) -> Tuple[bool, str]:
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found."

        camp.activities = self._normalize_activity_list(camp.activities)

        if not (0 <= activity_index < len(camp.activities)):
            return False, "Invalid activity index."

        activity = camp.activities[activity_index]
        current_ids = set(activity.campers)
        added_count = 0

        for camper in camp.campers:
            if camper.camper_id not in current_ids:
                activity.campers.append(camper.camper_id)
                added_count += 1

        if added_count > 0:
            self.camp_manager.update(camp)
            return True, f"Added {added_count} campers to '{activity.name}'."
        return False, "All campers are already in this activity."
