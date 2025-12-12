from datetime import date, datetime
import uuid
from typing import List, Tuple, Optional
from models.camp import Camp
from models.resource import Equipment

class CampService:
    """
    Service layer for Camp-related business logic.
    Responsible for validation, state changes, and coordinating data persistence.
    """
    def __init__(self, camp_manager):
        self.camp_manager = camp_manager

    def is_name_unique(self, name: str) -> bool:
        """Check if a camp name is unique across the system."""
        camps = self.camp_manager.read_all()
        return not any(c.name == name for c in camps)

    def validate_dates(self, start_date: date, end_date: date):
        """
        Validate camp dates business rules.
        Raises ValueError if invalid.
        """
        if start_date < datetime.now().date():
            raise ValueError("Start date cannot be in the past.")
        if end_date < start_date:
            raise ValueError(f"End date must be on or after start date ({start_date}).")

    def create_camp(self, name: str, location: str, camp_type: str, start_date: date, end_date: date, initial_food_stock: int) -> Camp:
        """
        Creates a new camp with full validation.
        """
        # 1. Final Validation
        if not name.strip():
            raise ValueError("Camp name cannot be empty.")
        
        if not self.is_name_unique(name):
             raise ValueError(f"Camp name '{name}' already exists.")
        
        self.validate_dates(start_date, end_date)

        if initial_food_stock < 0:
            raise ValueError("Initial food stock cannot be negative.")

        # 2. Create Object
        camp = Camp(
            camp_id=str(uuid.uuid4()),
            name=name,
            location=location,
            camp_type=camp_type,
            start_date=start_date,
            end_date=end_date,
            initial_food_stock=initial_food_stock,
        )

        # 3. Persist
        self.camp_manager.add(camp)
        
        return camp

    def top_up_food(self, camp_name: str, amount: int) -> Tuple[bool, str]:
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found."
        
        try:
            camp.add_food(amount)
            self.camp_manager.update(camp)
            return True, f"Food stock for camp '{camp.name}' has been topped up by {amount}."
        except ValueError as e:
            return False, str(e)

    def update_location(self, camp_name: str, new_location: str) -> Tuple[bool, str]:
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found."
        
        if not new_location.strip():
            return False, "Location cannot be empty."

        camp.location = new_location.strip()
        self.camp_manager.update(camp)
        return True, f"Location for '{camp.name}' updated to '{new_location}'."

    def get_conflicting_camps(self, leader_username: str, start_date: date, end_date: date, exclude_camp_id: str = None) -> List[Camp]:
        leader_camps = self.camp_manager.get_camps_by_leader(leader_username)
        conflicts = []

        for other_camp in leader_camps:
            if exclude_camp_id and other_camp.camp_id == exclude_camp_id:
                continue

            if Camp.dates_overlap(start_date, end_date, other_camp.start_date, other_camp.end_date):
                conflicts.append(other_camp)

        return conflicts

    def update_dates(self, camp_name: str, new_start: date, new_end: date, force_unassign_leader: bool = False) -> Tuple[bool, str, List[Camp]]:
        """
        Updates camp dates.
        Returns (success, message, conflicting_camps).
        If conflicts found and force_unassign_leader is False, returns (False, "Conflict", conflicts).
        If force_unassign_leader is True, unassigns leader and updates dates.
        """
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found.", []

        can_edit, reason = camp.can_edit_dates()
        if not can_edit:
            return False, reason, []

        try:
            self.validate_dates(new_start, new_end)
        except ValueError as e:
            return False, str(e), []

        if camp.camp_leader:
            conflicts = self.get_conflicting_camps(camp.camp_leader, new_start, new_end, camp.camp_id)
            if conflicts:
                if not force_unassign_leader:
                    return False, "Schedule conflict detected", conflicts
                else:
                    camp.camp_leader = None
        
        camp.start_date = new_start
        camp.end_date = new_end
        self.camp_manager.update(camp)
        
        return True, f"Dates for '{camp.name}' updated to {new_start} - {new_end}.", []

    def assign_leader(self, camp_name: str, leader_username: str) -> Tuple[bool, str]:
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found."
        
        # Check conflicts again to be safe
        conflicts = self.get_conflicting_camps(leader_username, camp.start_date, camp.end_date, camp.camp_id)
        if conflicts:
            conflict_names = ", ".join(c.name for c in conflicts)
            return False, f"Leader '{leader_username}' has conflicting camps: {conflict_names}"

        camp.camp_leader = leader_username
        self.camp_manager.update(camp)
        return True, f"Leader '{leader_username}' assigned to '{camp.name}'."

    def add_equipment(self, camp_name: str, name: str, target: int, current: int, condition: str) -> Tuple[bool, str]:
        camp = self.camp_manager.find_camp(camp_name)
        if not camp:
            return False, f"Camp '{camp_name}' not found."
        
        if target < 0 or current < 0:
            return False, "Quantities cannot be negative."

        new_eq = Equipment(
            resource_id=str(uuid.uuid4()),
            name=name,
            camp_id=camp.camp_id,
            target_quantity=target,
            current_quantity=current,
            condition=condition
        )
        
        camp.equipment.append(new_eq)
        self.camp_manager.update(camp)
        return True, f"Added {name} to {camp.name}."
