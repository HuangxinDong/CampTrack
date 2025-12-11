from .console_manager import console_manager
from .display_helper import DisplayHelper
from rich.align import Align
from rich.panel import Panel
from datetime import datetime, date, timedelta


class ConversationDisplay(DisplayHelper):
    """
    Handles display of conversation lists and threads.
    Now uses ConsoleManager for Rich output.
    """
    
    def display_list(self, summaries: list[dict]) -> None:
        """
        Display formatted conversation list.
        
        Args:
            summaries: List from get_conversation_summaries()
        """
        console_manager.print_header("YOUR CONVERSATIONS")
        
        table_rows = []
        for i, summary in enumerate(summaries, start=1):
            partner = summary['partner']
            unread = summary['unread_count']
            preview = summary['preview']
            
            # Build the unread badge
            badge = f"[bold red][{unread} new][/bold red]" if unread > 0 else ""
            
            # Create content for the panel
            content = f"[bold medium_purple1]{i}. {partner}[/bold medium_purple1] {badge}\n[dim]\"{preview}\"[/dim]"
            
            # Display as a panel
            console_manager.print_panel(content, style="blue")
        
        console_manager.print_message("═" * self.width)

    def display_chat_thread(self, partner: str, messages: list[dict], current_user: str) -> None:
        """
        Display full message thread with a specific partner.
        
        Args:
            partner: Username of the other person
            messages: List of message dicts
            current_user: Username of the viewer
        """
        console_manager.print_header(f"Chat with {partner}")
        
        # Use console_manager's console directly for advanced alignment
        console = console_manager.console

        if not messages:
            console_manager.print_info("(No messages yet)")
        else:
            # Sort messages just in case
            # Handle potential missing sent_at by defaulting to min time or similar, though DB should have it.
            # We assume sent_at is ISO string.
            messages.sort(key=lambda m: m.get('sent_at', ''))

            last_date = None
            today = date.today()
            yesterday = today - timedelta(days=1)

            for msg in messages:
                # 1. Parse Date/Time
                sent_at_str = msg.get('sent_at')
                timestamp_display = ""
                
                if sent_at_str:
                    try:
                        dt = datetime.fromisoformat(sent_at_str)
                        # Localize if necessary? For now assuming UTC/naive is fine or consistently handled.
                        msg_date = dt.date()
                        timestamp_display = dt.strftime("%H:%M")
                    except ValueError:
                        msg_date = None
                        timestamp_display = "??:??"
                else:
                    # Fallback if no sent_at (legacy messages?)
                    msg_date = None
                    timestamp_display = "??:??"

                # 2. Date Separator
                if msg_date and msg_date != last_date:
                    if msg_date == today:
                        date_label = "Today"
                    elif msg_date == yesterday:
                        date_label = "Yesterday"
                    else:
                        # Format like "October 24, 2025"
                        date_label = msg_date.strftime("%B %d, %Y")
                    
                    # Option 1 Style: Centered Text
                    console.print(Align.center(f"\n[bold dim]─── {date_label} ───[/bold dim]\n"))
                    last_date = msg_date

                # 3. Message Display
                is_me = msg['from_user'] == current_user
                content = msg['content']
                
                if is_me:
                    # Me: Right aligned, Medium Purple, Title Right
                    panel = Panel(
                        content,
                        title=f"[bold medium_purple1]Me ({timestamp_display})[/bold medium_purple1]",
                        title_align="right",
                        style="bold medium_purple1",
                        width=50,
                        border_style="medium_purple1"
                    )
                    console.print(Align.right(panel))
                else:
                    # Partner: Left aligned, Blue, Title Left
                    panel = Panel(
                        content,
                        title=f"[bold blue]{partner} ({timestamp_display})[/bold blue]",
                        title_align="left",
                        style="bold blue",
                        width=50,
                        border_style="blue"
                    )
                    console.print(Align.left(panel))
        
        console_manager.print_message("\n")
        console_manager.print_message("[italic dim](Press Enter to go back, or 'r' to reply)[/italic dim]")


# Default instance for easy import
conversation_display = ConversationDisplay()