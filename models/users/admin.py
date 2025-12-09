
from models.users.class_map import register
from models.users.users import User
from persistence.dao.user_manager import UserManager

@register("Admin")
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
        ]
        self.user_manager = UserManager()

    def handle_create_user(self):
        username = input("Enter username: ")
        password = input("Enter password: ")
        role = input("Enter role (Leader/Coordinator): ")
        
        success, message = self.user_manager.create_user(username, password, role)
        print(message)

    def handle_delete_user(self):
        username = input("Enter username to delete: ")
        success, message = self.user_manager.delete_user(username)
        print(message)

