# handlers/leader_handler.py
from datetime import datetime
from handlers.base_handler import BaseHandler


class LeaderHandler(BaseHandler):
    """Handles Leader-specific actions."""

    def __init__(self, user, user_manager, message_manager, camp_manager):
        super().__init__(user, user_manager, message_manager)
        self.camp_manager = camp_manager

    def get_all_camps_with_status(self):
        """
        Returns list of camps with their availability status.
        Returns list of (camp, status_string) tuples.
        """
        camps = self.camp_manager.read_all()
        result = []
        for camp in camps:
            if camp.camp_leader == self.user.username:
                status = "(You are the leader)"
            elif camp.camp_leader:
                status = f"(Assigned to: {camp.camp_leader})"
            else:
                status = "(Available)"
            result.append((camp, status))
        return result

    def get_my_camps(self):
        """Returns camps this leader supervises."""
        camps = self.camp_manager.read_all()
        return [c for c in camps if c.camp_leader == self.user.username]

    def assign_camp_to_self(self, camp):
        """
        Assign a camp to this leader.
        Returns (success: bool, message: str)
        """
        # Check if already assigned to someone else
        if camp.camp_leader and camp.camp_leader != self.user.username:
            return False, f"Cannot select '{camp.name}' - already assigned to {camp.camp_leader}"

        # Check for schedule conflicts
        my_camps = self.get_my_camps()
        new_start = camp.start_date if isinstance(camp.start_date, datetime) else datetime.strptime(str(camp.start_date), "%Y-%m-%d")
        new_end = camp.end_date if isinstance(camp.end_date, datetime) else datetime.strptime(str(camp.end_date), "%Y-%m-%d")

        for c in my_camps:
            s = datetime.strptime(str(c.start_date), "%Y-%m-%d") if isinstance(c.start_date, str) else c.start_date
            e = datetime.strptime(str(c.end_date), "%Y-%m-%d") if isinstance(c.end_date, str) else c.end_date
            if (new_start <= e) and (new_end >= s):
                return False, f"Cannot select '{camp.name}' - schedule conflicts with '{c.name}'."

        if camp.camp_leader == self.user.username:
            return False, f"You are already supervising '{camp.name}'"

        camp.assign_leader(self.user.username)
        self.camp_manager.update(camp)
        return True, f"You are now supervising: {camp.name}"

    def set_food_per_camper(self, camp_name, amount):
        """
        Set food per camper per day for a camp.
        Returns (success: bool, message: str)
        """
        camps = self.camp_manager.read_all()
        selected_camp = next((c for c in camps if c.name == camp_name), None)

        if not selected_camp:
            return False, "Camp not found."

        if selected_camp.camp_leader != self.user.username:
            return False, "You cannot edit a camp if you are not the leader."

        selected_camp.food_per_camper_per_day = amount
        self.camp_manager.update(selected_camp)
        return True, f"Food requirement updated for camp '{selected_camp.name}'."