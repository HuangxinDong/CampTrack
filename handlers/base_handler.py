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
            {"name": "View specific chat", "command": self.view_chat},
            {"name": "Placeholder 2", "command": self.send_new_message},
        ]


    def get_my_messages(self):
        """Returns list of messages for current user."""
        messages = self.message_manager.read_all()
        return [m for m in messages if m['to_user'] == self.user.username]


    @cancellable
    def view_messages(self):
        """
        View all messages for the current user.
        """
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
            
            # Try to match index
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.message_view_commands):
                    self.message_view_commands[idx]['command']()
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Invalid selection.")

    def view_chat(self):
        """
        Ask user for conversation number, validate, and show thread.
        """
        prompt = "Enter conversation number: "
        
        # We need to re-fetch summaries to know what the numbers mean
        # (This is slightly inefficient fetching twice but safe)
        messages = self.message_manager.read_all()
        summaries = get_conversation_summaries(messages, self.user.username)
        
        if not summaries:
            print("No conversations to view.")
            return

        try:
            choice = get_input(prompt)
            
            # Helper: Validates if input is a valid index for the list
            if not choice.isdigit():
                print("Invalid selection.")
                return

            idx = int(choice) - 1
            if idx < 0 or idx >= len(summaries):
                print("Invalid selection.")
                return
            
            # Valid selection -> Show thread
            partner = summaries[idx]['partner']
            
            # Filter messages for this partner
            chat = []
            for m in messages:
                if (m['from_user'] == self.user.username and m['to_user'] == partner) or \
                   (m['from_user'] == partner and m['to_user'] == self.user.username):
                    chat.append(m)

            # Mark unread messages as read (Batch Update)
            unread_ids = [m['message_id'] for m in chat 
                         if m['to_user'] == self.user.username and not m.get('mark_as_read', False)]
            
            if unread_ids:
                self.message_manager.mark_as_read_batch(unread_ids)

            conversation_display.display_chat_thread(partner, chat, self.user.username)
            
            # Wait for user before returning to menu
            get_input("")
            
        except Exception as e:
            from cli.input_utils import QuitException, BackException
            # If user presses 'b' in the chat, just return to the list
            if isinstance(e, BackException):
                return
            
            # If user presses 'q', let it bubble up to exit app
            if isinstance(e, QuitException):
                raise e
                
            print(f"Error viewing chat: {e}")

    def send_new_message(self):
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
