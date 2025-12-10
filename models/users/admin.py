
from models.users.class_map import register
from models.users.users import User

@register("Admin")
class Admin(User):
    """
    Admin model class. Inherits from User.
    Represents an administrator with full system access.
    """
    def __init__(self, username, password, role="Admin", enabled=True):
        super().__init__(username, password, role, enabled)
        self.user_manager = UserManager()

    def create_user(self, username, password, role, **kwargs):
        """
        Pure business logic to create a user.
        Returns (success, message).
        """
        return self.user_manager.create_user(username, password, role, **kwargs)

    def delete_user(self, username):
        """
        Pure business logic to delete a user.
        Returns (success, message).
        """
        return self.user_manager.delete_user(username)

    def toggle_status(self, username, enabled):
        """
        Pure business logic to toggle user status.
        Returns (success, message).
        """
        return self.user_manager.toggle_user_status(username, enabled)




