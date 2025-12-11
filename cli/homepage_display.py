from .console_manager import console_manager
from rich.panel import Panel
from rich.text import Text
from rich import box

class HomepageDisplay:
    """
    Handles display of the main homepage menu using Rich.
    """
    
    def display_home_menu(self, commands: list[dict], notifications: list[str] = None) -> None:
        """
        Display the main menu with optional notifications.
        
        Args:
            commands: List of command dictionaries (from handler)
            notifications: Optional alert strings (e.g. unread messages, system alerts)
        """
        # 1. Show Inbox if notifications exist
        if notifications:
            messages = []
            alerts = []
            
            # Categorize notifications
            for note in notifications:
                if not note: continue
                clean_note = note.strip()
                if "unread message" in clean_note.lower():
                    messages.append(clean_note)
                else:
                    alerts.append(clean_note)
            
            if messages or alerts:
                inbox_content = Text()
                
                # Messages Section
                if messages:
                    inbox_content.append(" ✉️  Messages\n", style="bold #FF69B4")
                    for msg in messages:
                        inbox_content.append(f"    • {msg}\n", style="white")
                    if alerts:
                        inbox_content.append("\n") # Spacer
                
                # Alerts Section
                if alerts:
                    inbox_content.append(" ⚠️  Alerts\n", style="bold #FF69B4")
                    for alert in alerts:
                        # Highlight Camp Name if possible (heuristic: text inside quotes or typical format)
                        # Current format often: "Camp 'Alpha' has..."
                        import re
                        # Bold quotes parts (Camp names)
                        formatted_alert = re.sub(r"'([^']*)'", r"[bold white]'\1'[/bold white]", alert)
                        inbox_content.append(f"    • ", style="white")
                        inbox_content.append(Text.from_markup(formatted_alert))
                        inbox_content.append("\n")

                console_manager.console.print(Panel(
                    inbox_content,
                    title="[bold #FF69B4] INBOX [/bold #FF69B4]",
                    border_style="#FF69B4",
                    box=box.ROUNDED,
                    width=60,
                    padding=(0, 1)
                ))
                console_manager.console.print("") # Spacing

        # 2. Format commands for display
        menu_items = []
        for i, cmd in enumerate(commands):
            menu_items.append(f"[bold medium_purple1]{i + 1}.[/bold medium_purple1] {cmd['name']}")
            
        # 3. Print the menu using console_manager
        console_manager.print_header("MAIN MENU")
        
        # We can use print_menu (which puts it in a panel)
        console_manager.print_menu(
            "", 
            menu_items
        )
        
        # 4. Instructions (Outside the panel to prevent cutoff)
        console_manager.print_message("\n[bold medium_purple1]Type the number of the command, or 'q' to quit[/bold medium_purple1]")

# Default instance
homepage_display = HomepageDisplay()
