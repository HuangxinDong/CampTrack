# handlers/coordinator_handler.py
from datetime import datetime
from models.camp import Camp
from handlers.base_handler import BaseHandler
from cli.input_utils import get_input, cancellable
from cli.prompts import get_positive_int


class CoordinatorHandler(BaseHandler):
    """Handles Coordinator-specific actions."""

    def __init__(self, user, user_manager, message_manager, camp_manager):
        super().__init__(user, user_manager, message_manager)
        self.camp_manager = camp_manager
        self.commands = self.parent_commands + [
            {"name": "Create Camp", "command": self.create_camp},
            {"name": "Edit Camp", "command": self.edit_camp_resources},
            {
                "name": "Set Daily Payment Limit",
                "command": self.set_daily_payment_limit,
            }
        ]

    @cancellable
    def create_camp(self):
        name = get_input('Enter camp name: ')
        location = get_input('Enter camp location: ')
        camp_type = get_input('Enter camp type: ')

        while True:
            start_date_str = get_input('Enter camp start date (yyyy-mm-dd): ')
            end_date_str = get_input('Enter camp end date (yyyy-mm-dd): ')
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                if end_date < start_date:
                    print("Error: End date must be after start date.")
                    continue
                break
            except ValueError:
                print("Error: Invalid date format. Please use yyyy-mm-dd.")

        food = get_positive_int('Enter camp food stock: ')
        
        camp = Camp(name, location, camp_type, start_date, end_date, food)
        self.camp_manager.add(camp)
        print(f"Camp '{name}' created successfully.")

    def edit_camp_resources(self):
        self.commands = [
            {"name": "Top Up Food Stock", "command": self.top_up_food_stock},
        ]

    @cancellable
    def top_up_food_stock(self):
        camp_name = get_input("Enter the camp name to top up food stock for: ")
        camps = self.camp_manager.read_all()
        selected_camp = next((camp for camp in camps if camp.name == camp_name), None)
        if not selected_camp:
            print('Camp not found')
            return
        additional_food = get_positive_int("Enter the amount of food to add: ")
        selected_camp.topup_food(additional_food)
        self.camp_manager.update(selected_camp)
        print(f"Food stock for camp '{camp_name}' has been topped up by {additional_food}.")
        self.commands = self.parent_commands

    @cancellable
    def set_daily_payment_limit(self):
        scout_leader_name = get_input("Enter the name of the scout leader: ")

        scout_leader = self.user_manager.find_user(scout_leader_name)
        if scout_leader is None:
            print('Cannot find user')
            return
        if scout_leader['role'] != 'Leader':
            print('User is not a leader')
            return
        
        daily_payment_rate = get_positive_int("Enter the new daily payment rate: ")
        self.user_manager.update_daily_payment_rate(scout_leader['username'], daily_payment_rate)
        print(f"Daily payment rate updated for {scout_leader_name}.")