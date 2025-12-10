"""Main user interface for command processing."""

from utils.input_helpers import get_input, QuitException, BackException


class MainUI:
    """
    Handles the main command loop and user interaction.
    
    Processes user commands and manages navigation between menus.
    """
    
    def __init__(self):
        pass
    
    def process_command(self, user) -> bool:
        """
        Display commands and process user selection.
        
        Args:
            user: The logged-in user object
            
        Returns:
            True to continue the loop, False to exit the app
        """
        user.display_commands()
        
        try:
            user_input = get_input("Please enter a number\n> ")
        except QuitException:
            print("Goodbye!")
            return False
        except BackException:
            user.commands = user.parent_commands
            return True
        
        try:
            user_input_as_int = int(user_input)
        except ValueError:
            print("Please enter a valid number.")
            return True
        
        # Validate range
        if user_input_as_int < 1 or user_input_as_int > len(user.commands):
            print("Please enter a number from the list.")
            return True
        
        user.process_command(user_input_as_int)
        return True


# Default instance for easy import
main_ui = MainUI()