# handlers/coordinator_handler.py
from datetime import datetime
from models.camp import Camp
from handlers.base_handler import BaseHandler
from cli.input_utils import get_input, cancellable
from cli.prompts import get_positive_int
from cli.coordinator_display import coordinator_display
import cli.visualisations as visualisations

class CoordinatorHandler(BaseHandler):
    """Handles Coordinator-specific actions."""

    def __init__(self, user, context):
        super().__init__(user, context)

        self.commands = self.parent_commands + [
            {"name": "Create Camp", "command": self.create_camp},
            {"name": "Edit Camp", "command": self.edit_camp_resources},
            {
                "name": "Set Daily Payment Limit",
                "command": self.set_daily_payment_limit,
            },
            {"name": "See Visualizations", "command": self.visualization_menu},
        ]

        self.main_commands = self.commands.copy()

    @cancellable
    def create_camp(self):
        name = get_input("Enter camp name: ")
        location = get_input("Enter camp location: ")
        camp_type = get_input("Enter camp type: ")

        while True:
            start_date_str = get_input("Enter camp start date (yyyy-mm-dd): ")
            end_date_str = get_input("Enter camp end date (yyyy-mm-dd): ")
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                
                if start_date < datetime.now().date():
                    print("Error: Start date cannot be in the past.")
                    continue

                if end_date < start_date:
                    print("Error: End date must be after start date.")
                    continue
                break
            except ValueError:
                print("Error: Invalid date format. Please use yyyy-mm-dd.")

        food = get_positive_int("Enter camp food stock: ")

        camp = Camp(
            camp_id=None,
            name=name,
            location=location,
            camp_type=camp_type,
            start_date=start_date,
            end_date=end_date,
            current_food_stock=food,
        )
        self.context.camp_manager.add(camp)
        # Use new display class for success message
        coordinator_display.display_camp_creation_success(camp)

    def edit_camp_resources(self):
        self.commands = [
            {"name": "Top Up Food Stock", "command": self.top_up_food_stock},
        ]

    @cancellable
    def top_up_food_stock(self):
        camps = self.context.camp_manager.read_all()
        if not camps:
            print("No camps available.")
            return

        print("Camps:")
        # Use new display class for camp list
        coordinator_display.display_camp_list(camps)


        while True:
            invalid_selection_error_message = 'Please select a number from the list'
            selection = get_input("\nEnter camp number to topup food:")
            if not selection.isdigit():
                print(invalid_selection_error_message)
                continue
            selected_number = int(selection)
            if not (1 <= selected_number <= len(camps)):
                print(invalid_selection_error_message)
                continue
            break



        selected_camp = camps[selected_number -1]
        if not selected_camp:
            print("Camp not found")
            return
        additional_food = get_positive_int("Enter the amount of food to add: ")
        try:
            selected_camp.add_food(additional_food)
            self.context.camp_manager.update(selected_camp)
            
            from cli.console_manager import console_manager
            console_manager.print_success(f"Food stock for camp '{selected_camp.name}' has been topped up by {additional_food}.")
            get_input("(Press Enter to continue)")
        except ValueError as e:
            from cli.console_manager import console_manager
            console_manager.print_error(f"Error: {e}")
            
        self.commands = self.main_commands

    @cancellable
    def set_daily_payment_limit(self):
        scout_leader_name = get_input("Enter the name of the scout leader: ")

        scout_leader = self.context.user_manager.find_user(scout_leader_name)
        if scout_leader is None:
            print("Cannot find user")
            return
        if scout_leader["role"] != "Leader":
            print("User is not a leader")
            return

        old_rate = scout_leader.get("daily_restock_limit", 0) # Assumed key, checking user model would be safer, but relying on context logic often used. 
        # Actually daily_payment_rate for Leader... checking user_manager usage.
        # user_manager.update_daily_payment_rate updates 'daily_payment_rate'
        old_rate = scout_leader.get("daily_payment_rate", "N/A")

        daily_payment_rate = get_positive_int("Enter the new daily payment rate: ")
        self.context.user_manager.update_daily_payment_rate(scout_leader["username"], daily_payment_rate)
        
        coordinator_display.display_payment_update_success(scout_leader_name, old_rate, daily_payment_rate)

    def restore_main_commands(self):
        self.commands = self.main_commands

    def visualization_menu(self):
        self.commands = [
             {'name': 'Show Food Stock Chart', 'command': lambda:
             visualisations.plot_food_stock(self.context.camp_manager)},
             {'name': 'Show Campers per Camp Chart', 'command': lambda:
               visualisations.plot_campers_per_camp(self.context.camp_manager)}, 
             {'name': 'Show Location Distribution', 'command': lambda:
              visualisations.plot_camp_location_distribution(self.context.camp_manager)},]
            
