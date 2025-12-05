from models.users.users import User

class Leader(User):
    def __init__(self, username, password, role, enabled, daily_payment_rate):
        super().__init__(username, password, role, enabled)
        self.daily_payment_rate = daily_payment_rate

    def to_dict(self):
        data = super().to_dict()
        data['daily_payment_rate'] = self.daily_payment_rate
        return data