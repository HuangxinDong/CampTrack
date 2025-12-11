"""Centralized input handling with quit/back support."""

from functools import wraps


class QuitException(Exception):
    """Raised when user wants to quit the application."""
    pass


class BackException(Exception):
    """Raised when user wants to go back/cancel current operation."""
    pass


class InputHandler:
    """
    Handles user input with built-in quit and back support.
    
    Attributes:
        quit_char: Character that triggers quit (default 'q')
        back_char: Character that triggers back (default 'b')
    """
    
    def __init__(self, quit_char: str = 'q', back_char: str = 'b'):
        self.quit_char = quit_char
        self.back_char = back_char
    
    def get_input(self, prompt: str) -> str:
        """
        Get user input with quit/back support.
        
        Args:
            prompt: The prompt to display
            
        Returns:
            The user's input string
            
        Raises:
            QuitException: If user enters quit character
            BackException: If user enters back character
        """
        if prompt:
             # Use console_manager for styled input
             from cli.console_manager import console_manager
             value = console_manager.input(prompt)
        else:
             value = input("")
        
        if value.lower() == self.quit_char:
            raise QuitException()
        
        if value.lower() == self.back_char:
            raise BackException()
        
        return value


def cancellable(func):
    """
    Decorator that handles BackException automatically.
    If user presses back, prints 'Cancelled.' and returns None.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BackException:
            print("Cancelled.")
            return None
    return wrapper


# Default instance for easy import
input_handler = InputHandler()
get_input = input_handler.get_input