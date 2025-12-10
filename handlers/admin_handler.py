from handlers.base_handler import BaseHandler

class AdminHandler(BaseHandler):
    """Handles Admin-specific actions."""
    def __init__(self, user, user_manager, message_manager, camp_manager):
        super().__init__(user, user_manager, message_manager)
        self.camp_manager = camp_manager  # Admin might need this later

    def create_user(self, username, password, role):
        """
        Create a new user.
        Returns (success: bool, message: str)
        """
        return self.user_manager.create_user(username, password, role)

    def delete_user(self, username):
        """
        Delete a user.
        Returns (success: bool, message: str)
        """
        return self.user_manager.delete_user(username)