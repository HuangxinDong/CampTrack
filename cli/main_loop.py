# cli/main_loop.py
"""Main program loop and command processing."""

from cli.input_utils import get_input, QuitException, BackException


def display_menu(handler):
    """Display available commands for the handler."""
    for i, command in enumerate(handler.commands):
        print(f"{i + 1}. {command['name']}")


def get_menu_choice():
    """Get handler's menu selection. Raises QuitException or BackException."""
    return get_input("Please enter a number or press q to quit or b for back to homepage.\n> ")


def run_program(user, handler):
    """Main program loop."""
    running = True
    
    while running:
        display_menu(handler)
        
        try:
            handler_input = get_menu_choice()
        except QuitException:
            print("Goodbye!")
            break
        except BackException:
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
        
    
        handler.commands[choice - 1]["command"]()
