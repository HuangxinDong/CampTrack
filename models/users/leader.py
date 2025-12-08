from data.camp_manager import CampManager
from models.users.class_map import register
from models.users.users import User
from program.helpers import get_positive_int

@register("Leader")
class Leader(User):
    def __init__(self, username, password, role, enabled, daily_payment_rate):
        super().__init__(username, password, role, enabled)
        self.daily_payment_rate = daily_payment_rate
        self.parent_commands = [
            {'name': 'Edit Camp', 'command': self.create_camp},
        ]
        self.commands = self.parent_commands
        self.camp_manager = CampManager()

    def edit_camp(self):
        self.commands = [
            {'name': 'Assign food per camper per day', 'command': self.top_up_food_stock},
        ]

    def assign_food_per_camper_per_day(self):
        camp_name = input("Enter the camp name to top up food stock for: ")
        camps = self.camp_manager.read_all()
        selected_camp = next((camp for camp in camps if camp.name == camp_name), None)

        if not selected_camp:
            print('Camp not found')
            return
        
        if selected_camp.camp_leader != self.username:
            print('You cannot edit a camp if you are not a leader. Ask coordinator to add you.')
            return
        
        food_per_camper_per_day = get_positive_int('Enter foor per camper per day: ')
        
        selected_camp.food_per_camper_per_day = food_per_camper_per_day
        
        self.commands = self.parent_commands
    

    def to_dict(self):
        data = super().to_dict()
        data['daily_payment_rate'] = self.daily_payment_rate
        return data