from datetime import datetime
from data.camp_manager import CampManager
from models.camp import Camp
from models.users.class_map import register
from models.users.users import User
from data.user_manager import UserManager
from program.helpers import get_positive_int

@register("Coordinator")
class Coordinator(User):
    def __init__(self, username, password, role="Coordinator", enabled=True):
        super().__init__(username, password, role, enabled)
        self.parent_commands = [
            {'name': 'Create Camp', 'command': self.create_camp},
            {'name': 'Edit Camp', 'command': self.edit_camp},
            {'name': 'Set Daily Payment Limit', 'command': self.set_daily_payment_limit},
        ]
        self.commands = self.parent_commands
        self.camp_manager = CampManager()
        self.user_manager = UserManager()

    def create_camp(self):
        name = input('Enter camp name: ')
        location = input('Enter camp location: ')
        camp_type = input('Enter camp type: ')

        while True:
            start_date_str = input('Enter camp start date (yyyy-mm-dd): ')
            end_date_str = input('Enter camp end date (yyyy-mm-dd): ')
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
    
    def edit_camp(self):
        self.commands = [
            {'name': 'Top Up Food Stock', 'command': self.top_up_food_stock},
        ]
    
    def top_up_food_stock(self):
        camp_name = input("Enter the camp name to top up food stock for: ")
        camps = self.camp_manager.read_all()
        selected_camp = next((camp for camp in camps if camp.name == camp_name), None)
        if not selected_camp:
            print('Camp not found')
            return
        additional_food = int(input("Enter the amount of food to add: "))
        selected_camp.topup_food(additional_food)
        self.camp_manager.update(selected_camp)
        print(f"Food stock for camp '{camp_name}' has been topped up by {additional_food}.")
        self.commands = self.parent_commands
        return


    def set_daily_payment_limit(self):
        scout_leader_name = input("Enter the name of the scout leader: ")

        scout_leader = self.user_manager.find_user(scout_leader_name)
        if scout_leader is None:
            print('Cannot find user')
            return
        if scout_leader['role'] != 'Leader':
            print('User is not a leader')
            return
        
        daily_payment_rate = input("Enter the new daily payment rate: ")

        try:
            daily_payment_rate_as_int = int(daily_payment_rate)
        except ValueError:
            print("Not a valid number")
            return

        self.user_manager.update_daily_payment_rate(scout_leader['username'], daily_payment_rate_as_int)

