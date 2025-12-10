from handlers.base_handler import BaseHandler
from cli.input_utils import get_input, cancellable


class AdminHandler(BaseHandler):
    """Handles Admin-specific actions."""
    def __init__(self, user, user_manager, message_manager, camp_manager):
        super().__init__(user, user_manager, message_manager)
        self.camp_manager = camp_manager  # Admin might need this later

        self.commands = self.parent_commands + [
            {"name": "Create User", "command": self.handle_create_user},
            {"name": "Delete User", "command": self.handle_delete_user},
        ]

        self.main_commands = self.commands.copy()


    @cancellable 
    def handle_create_user(self):
        username = get_input("Enter username: ")
        password = get_input("Enter password: ")
        role = get_input("Enter role (Leader/Coordinator): ")
        
        success, message = self.user_manager.create_user(username, password, role)
        print(message)


    @cancellable 
    def handle_delete_user(self):
        username = get_input("Enter username to delete: ")
        success, message = self.user_manager.delete_user(username)
        print(message)