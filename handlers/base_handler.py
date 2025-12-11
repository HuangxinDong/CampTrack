import uuid
from models.message import Message
from cli.input_utils import get_input, cancellable
from handlers.message_handler import get_conversation_summaries
from cli.chat_display import conversation_display


class BaseHandler:
    """Handles actions available to ALL user types."""
    
    def __init__(self, user, user_manager, message_manager):
        self.user = user
        self.user_manager = user_manager
        self.message_manager = message_manager

        self.parent_commands = [
            {"name": "View messages", "command": self.view_messages},
            {"name": "Send message", "command": self.send_message},
        ]
        self.commands = self.parent_commands.copy()
        self.main_commands = self.commands.copy()

        self.message_view_commands = [
            {"name": "Placeholder 1", "command": self._placeholder_1},
            {"name": "Placeholder 2", "command": self._placeholder_2},
        ]


    def get_my_messages(self):
        """Returns list of messages for current user."""
        messages = self.message_manager.read_all()
        return [m for m in messages if m['to_user'] == self.user.username]


    @cancellable
    def view_messages(self):
        while True:
            messages = self.message_manager.read_all()
            summaries = get_conversation_summaries(messages, self.user.username)
            
            if not summaries:
                print("No conversations.")
                return
            
            conversation_display.display_list(summaries)
            
            # Dynamic Menu Display
            for i, cmd in enumerate(self.message_view_commands):
                print(f"{i + 1}. {cmd['name']}")
            print("Enter number, 'b' to go back, or 'q' to quit: ")
            
            choice = get_input("")
            
            if choice == 'b':
                break
            elif choice.lower() == 'q':
                # Re-raising or letting get_input handle it if it wasn't caught
                # But typically main loop handles 'q'. Here we just break to return to main loop?
                # Actually, standard pattern in this app is usually returning or raising exceptions.
                # get_input usually raises QuitException if we enforce it. 
                # For safety, let's treat 'q' same as 'b' for this sub-loop or 
                # let it bubble up if get_input handles it.
                # However, since get_input returns 'q' if not handled, we should respect it.
                import sys
                print("Goodbye!")
                sys.exit(0) 

            # Try to match index
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.message_view_commands):
                    self.message_view_commands[idx]['command']()
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Invalid selection.")

    def _placeholder_1(self):
        print("Placeholder 1 executed")

    def _placeholder_2(self):
        print("Placeholder 2 executed")

    
    @cancellable
    def send_message(self, recipient_username=None):
        # If no recipient provided, ask for one
        if recipient_username is None:
            recipient_username = get_input('Enter the username for recipient: ')

        # Validate: can't message yourself
        if recipient_username == self.user.username:
            print('You cannot send a message to yourself.')
            return

        # Validate: recipient must exist
        recipient = self.user_manager.find_user(recipient_username)
        if not recipient:
            print('This user does not exist, please try again.')
            return

        message_content = get_input('Enter your message: ')

        message = Message(str(uuid.uuid4()), self.user.username, recipient['username'], message_content)

        try:
            self.message_manager.add(message.to_dict())
            print("Message sent successfully.")
        except Exception as e:
            print("Failed to send message. Please try again later.")
