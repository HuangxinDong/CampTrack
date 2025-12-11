from .console_manager import console_manager

class StartupDisplay:
    """
    Handles the display of the application startup screen.
    """
    
    def display_welcome_banner(self):
        """
        Displays a large welcome banner on startup.
        """
        # Generated ASCII art for "SCOUT CAMP" (One Line)
        # Generated ASCII art for "SCOUT CAMP" (Slant Font)
        banner_text = (
            r"   _____                 __     ______" + "\n"
            r"  / ___/_________  __  / /_   / ____/___ _____ ___  ____ " + "\n"
            r"  \__ \/ ___/ __ \/ / / / __/  / /   / __ `/ __ `__ \/ __ \ " + "\n"
            r" ___/ / /__/ /_/ / /_/ / /_   / /___/ /_/ / / / / / / /_/ / " + "\n"
            r"/____/\___/\____/\__,_/\__/   \____/\__,_/_/ /_/ /_/ .___/ " + "\n"
            r"                                                  /_/      " + "\n"
            "\n[bold white]CAMPSITE MANAGEMENT SYSTEM[/bold white]"
        )
        
        console_manager.print_banner(
            banner_text, 
            style="bold medium_purple1",
            title="WELCOME"
        )
        console_manager.print_message("\n")

# Default instance
startup_display = StartupDisplay()
