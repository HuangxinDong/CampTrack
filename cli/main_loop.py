# cli/main_loop.py
"""Main program loop and command processing."""
from cli.input_utils import get_input, QuitException, BackException

HOME_PROMPT = "> "
SUBMENU_PROMPT = "> "
  

from cli.homepage_display import homepage_display

def display_menu(handler):
    """Display available commands for the handler using HomepageDisplay."""
    # Check for notifications (e.g., Unread Messages)
    notifications=None
    if hasattr(handler, 'get_notifications'):
        notifications = handler.get_notifications()

    homepage_display.display_home_menu(handler.commands, notifications=notifications)


def get_menu_choice(prompt):
    """Get handler's menu selection. Raises QuitException or BackException."""
    return get_input(prompt)


def run_program(user, handler):
    """Main program loop."""
    running = True
    
    while running:
        display_menu(handler)
        
        is_home = handler.commands == handler.main_commands
        prompt = HOME_PROMPT if is_home else SUBMENU_PROMPT
        
        try:
            handler_input = get_menu_choice(prompt)
        except QuitException:
            print("Goodbye!")
            break
        except BackException:
            if is_home:
                print("You are already on the homepage.")
                continue
            handler.commands = handler.main_commands
            continue 

        try:
            choice = int(handler_input)
        except ValueError:
            print("Please enter a valid number.")
            continue
        
        if choice < 1 or choice > len(handler.commands):
            print("Please enter a number from the list.")
            continue
        
        try:
            handler.commands[choice - 1]["command"]()
        except QuitException:
            print("Goodbye!")
            break
