# cli/main_loop.py
"""Main program loop and command processing."""

from cli.input_utils import get_input, QuitException, BackException


def display_menu(user):
    """Display available commands for the user."""
    for i, command in enumerate(user.commands):
        print(f"{i + 1}. {command['name']}")


def get_menu_choice():
    """Get user's menu selection. Raises QuitException or BackException."""
    return get_input("Please enter a number\n> ")


def run_program(user, handler):
    """Main program loop."""
    running = True
    
    while running:
        display_menu(user)
        
        try:
            user_input = get_menu_choice()
        except QuitException:
            print("Goodbye!")
            break
        except BackException:
            user.commands = user.parent_commands
            continue
        
        try:
            choice = int(user_input)
        except ValueError:
            print("Please enter a valid number.")
            continue
        
        if choice < 1 or choice > len(user.commands):
            print("Please enter a number from the list.")
            continue
        
        # Still using old method for now
        user.process_command(choice)