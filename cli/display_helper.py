class DisplayHelper:
    """
    Base class for CLI display formatting.
    Kept for backward compatibility but now delegates to console_manager.
    """
    
    def __init__(self, width: int = 43):
        self.width = width
    
    def print_header(self, title: str) -> None:
        """Print a formatted header box."""
        console_manager.print_header(title)
    
    def print_footer(self) -> None:
        """Print a footer line."""
        console_manager.print_message("═" * self.width)