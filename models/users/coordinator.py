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
        pass