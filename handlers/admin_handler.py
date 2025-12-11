import uuid
from handlers.base_handler import BaseHandler
from cli.input_utils import get_input, cancellable
from models.announcement import Announcement
from persistence.dao.system_notification_manager import SystemNotificationManager



class AdminHandler(BaseHandler):
    """Handles Admin-specific actions."""
    def __init__(self, user, context):
        # Pass context to BaseHandler
        super().__init__(user, context)


        self.commands = self.parent_commands + [
            {"name": "Create User", "command": self.handle_create_user},
            {"name": "Delete User", "command": self.handle_delete_user},
            {"name": "Post announcement", "command": self.post_announcement},
            {"name": "Update Password", "command": self.handle_update_password},
        ]

        self.main_commands = self.commands.copy()


    @cancellable 
    def handle_create_user(self):
        username = get_input("Enter username: ")
        password = get_input("Enter password: ")
        
        success, message = self.context.user_manager.create_user(username, password)
        print(message)


    @cancellable 
    def handle_delete_user(self):
        username = get_input("Enter username to delete: ")
        success, message = self.context.user_manager.delete_user(username)
        print(message)

    @cancellable 
    def handle_update_password(self):
        username = get_input("Enter username to update password: ")
        new_password = get_input("Enter new password: ")
        success, message = self.context.user_manager.update_password(username, new_password)
        print(message)


    @cancellable
    def post_announcement(self):
        """Post a new global announcement."""
        print("Posting new announcement (visible to all users).")
        content = get_input("Enter content: ")
        
        announcement = Announcement(
            announcement_id=str(uuid.uuid4()),
            author=self.user.username,
            content=content
        )
        
        try:
            # This assumes self.context.announcement_manager exists and has an 'add' method
            # If not, the user needs to ensure it's initialized in __init__
            if self.context.announcement_manager:
                self.context.announcement_manager.add(announcement.to_dict())
                print("Announcement posted successfully.")
            else:
                print("Error: Announcement manager not initialized.")
        except Exception as e:
            print(f"Error posting announcement: {e}")