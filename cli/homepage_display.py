from .console_manager import console_manager

class HomepageDisplay:
    """
    Handles display of the main homepage menu using Rich.
    """
    
    def display_home_menu(self, commands: list[dict], notifications: list[str] = None) -> None:
        """
        Display the main menu with optional notifications.
        
        Args:
            commands: List of command dictionaries (from handler)
            notification: Optional alert string (e.g. unread messages)
        """
        # 1. Show notification if present
        if notifications:
            for notification in notifications:
                if notification:
                    console_manager.print_panel(f'*** {notification.strip()} ***', style="bold red")

        # 2. Format commands for display
        # We want a nice list like:
        # 1. View messages
        # 2. Send message
        # ...
        
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
