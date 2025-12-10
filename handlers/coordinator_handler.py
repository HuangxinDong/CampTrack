# handlers/coordinator_handler.py
from datetime import datetime
from models.camp import Camp
from handlers.base_handler import BaseHandler


class CoordinatorHandler(BaseHandler):
    """Handles Coordinator-specific actions."""

    def __init__(self, user, user_manager, message_manager, camp_manager):
        super().__init__(user, user_manager, message_manager)
        self.camp_manager = camp_manager

    def create_camp(self, name, location, camp_type, start_date, end_date, food):
        """
        Create a new camp.
        Returns (success: bool, message: str)
        """
        if end_date < start_date:
            return False, "End date must be after start date."

        camp = Camp(name, location, camp_type, start_date, end_date, food)
        self.camp_manager.add(camp)
        return True, f"Camp '{name}' created successfully."

    def top_up_food_stock(self, camp_name, amount):
        """
        Top up food stock for a camp.
        Returns (success: bool, message: str)
        """
        camps = self.camp_manager.read_all()
        selected_camp = next((c for c in camps if c.name == camp_name), None)
        
        if not selected_camp:
            return False, "Camp not found."

        selected_camp.topup_food(amount)
        self.camp_manager.update(selected_camp)
        return True, f"Food stock for camp '{camp_name}' topped up by {amount}."

    def set_daily_payment_rate(self, leader_username, rate):
        """
        Set daily payment rate for a leader.
        Returns (success: bool, message: str)
        """
        leader = self.user_manager.find_user(leader_username)
        
        if leader is None:
            return False, "Cannot find user."
        
        if leader['role'] != 'Leader':
            return False, "User is not a leader."

        return self.user_manager.update_daily_payment_rate(leader_username, rate)
