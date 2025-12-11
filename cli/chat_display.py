class DisplayHelper:
    """
    Base class for CLI display formatting.
    
    Attributes:
        width: Width of display elements (default 43)
    """
    
    def __init__(self, width: int = 43):
        self.width = width
    
    def print_header(self, title: str) -> None:
        """Print a formatted header box."""
        print("═" * self.width)
        print(f"  {title}")
        print("═" * self.width)
    
    def print_footer(self) -> None:
        """Print a footer line."""
        print("═" * self.width)


class ConversationDisplay(DisplayHelper):
    """
    Handles display of conversation lists and threads.
    Inherits formatting from DisplayHelper.
    """
    
    def display_list(self, summaries: list[dict]) -> None:
        """
        Display formatted conversation list.
        
        Args:
            summaries: List from get_conversation_summaries()
        """
        self.print_header("YOUR CONVERSATIONS")
        
        for i, summary in enumerate(summaries, start=1):
            partner = summary['partner']
            unread = summary['unread_count']
            preview = summary['preview']
            
            # Build the unread badge
            badge = f"[{unread} new]" if unread > 0 else ""
            
            # Print partner name with badge
            print(f"  {i}. {partner:<20} {badge:>12}")
            
            # Print preview on next line
            print(f"     \"{preview}\"")
            print()
        
        self.print_footer()
        # print("Enter conversation number (0 to go back, q to quit): ")


# Default instance for easy import
conversation_display = ConversationDisplay()