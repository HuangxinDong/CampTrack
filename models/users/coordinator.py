from data.camp_manager import CampManager
from models.camp import Camp
from models.users.users import User

class Coordinator(User):
    def __init__(self, username, password, role="Coordinator", enabled=True):
        super().__init__(username, password, role, enabled)
        self.commands = [
            {'name': 'Create Camp', 'command': self.create_camp},
            {'name': 'Edit Camp', 'command': self.edit_camp},
        ]
        self.camp_manager = CampManager()

    def create_camp(self):
        name = input('Enter camp name: ')
        location = input('Enter camp location: ')
        camp_type = input('Enter camp type: ')
        start_date = input('Enter camp start date (yyyy-mm-dd): ')
        end_date = input('Enter camp end date (yyyy-mm-dd): ')
        food = input('Enter camp food stock: ')

        camp = Camp(name, location, camp_type, start_date, end_date, food)
        self.camp_manager.add(camp)
    
    def edit_camp(self):
        self.commands = [
            {'name': 'Top Up Food Stock', 'command': self.top_up_food_stock},
            {'name': 'Set Daily Payment Limit', 'command': self.set_daily_payment_limit},
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
        return


    def set_daily_payment_limit(self):
        pass

