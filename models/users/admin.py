from models.users.users import User

class Admin(User):
    """
    Admin model class. Inherits from User.
    Represents an administrator with full system access.
    """
    def __init__(self, username, password, role="Admin", enabled=True):
        super().__init__(username, password, role, enabled)
        self.commands = [
            { 'name': 'Create User', 'command': self.handle_create_user },
            { 'name': 'Delete User', 'command': self.handle_delete_user },
            { 'name': 'Command 3', 'command': self.command_3 },
        ]

    def handle_create_user(self):
        print('Create user')

    def handle_delete_user(self):
        print('Delete User')

    def command_3(self):
        print('Command 3 User')
