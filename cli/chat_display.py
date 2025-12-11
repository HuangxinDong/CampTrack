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

    def display_chat_thread(self, partner: str, messages: list[dict], current_user: str) -> None:
        """
        Display full message thread with a specific partner.
        
        Args:
            partner: Username of the other person
            messages: List of message dicts
            current_user: Username of the viewer
        """
        self.print_header(f"Chat with {partner}")
        
        if not messages:
            print("  (No messages yet)")
        else:
            for msg in messages:
                sender = "Me" if msg['from_user'] == current_user else partner
                timestamp = msg.get('timestamp', '')
                content = msg['content']
                print(f"  [{timestamp}] {sender}: {content}")
        
        self.print_footer()
        print("(Press Enter to go back, or 'r' to reply)")


# Default instance for easy import
conversation_display = ConversationDisplay()