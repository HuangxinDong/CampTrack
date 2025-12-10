
from models.users.class_map import register
from models.users.users import User
from persistence.dao.user_manager import UserManager
from interface.interface_admin import AdminInterface

@register("Admin")
class Admin(User):
    """
    Admin model class. Inherits from User.
    Represents an administrator with full system access.
    """
    def __init__(self, username, password, role="Admin", enabled=True):
        super().__init__(username, password, role, enabled)
        self.user_manager = UserManager()
        self.commands = [
            { 'name': 'Create User', 'command': self.create_user },
            { 'name': 'Delete User', 'command': self.delete_user },
            { 'name': 'Toggle User Status', 'command': self.toggle_status },
        ]

    def create_user(self):
        username, password, role, kwargs = AdminInterface.get_user_details()
        success, message = self.user_manager.create_user(username, password, role, **kwargs)
        AdminInterface.show_message(message)

    def delete_user(self):
        username = AdminInterface.get_username_to_delete()
        success, message = self.user_manager.delete_user(username)
        AdminInterface.show_message(message)

    def toggle_status(self):
        username, enabled = AdminInterface.get_status_toggle_details()
        success, message = self.user_manager.toggle_user_status(username, enabled)
        AdminInterface.show_message(message)


