from persistence.dao.camp_manager import CampManager
from models.users.class_map import register
from models.users.users import User
from cli.prompts import get_positive_int
from datetime import datetime


@register("Leader")
class Leader(User):
    def __init__(self, username, password, role, enabled, daily_payment_rate):
        super().__init__(username, password, role, enabled)
        self.daily_payment_rate = daily_payment_rate
        self.parent_commands = [
            {'name': 'Select Camps to Supervise', 'command': self.select_camps_to_supervise},
            {'name': 'Edit Camp', 'command': self.edit_camp},
        ]
        self.commands = self.parent_commands
        self.camp_manager = CampManager()
    

    def to_dict(self):
        data = super().to_dict()
        data['daily_payment_rate'] = self.daily_payment_rate
        return data