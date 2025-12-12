"""
Centralized Console Manager using Rich library.
Handles all styled output for the application.
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.style import Style
from typing import List, Any, Optional

# Custom theme for consistent styling
custom_theme = Theme({
    "info": "blue",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold medium_purple1",
    "header": "bold white on blue",
    "highlight": "medium_purple1"
})

class ConsoleManager:
    """
    Singleton class to manage all CLI output using Rich.
    """
    _instance = None
    console: Console

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConsoleManager, cls).__new__(cls)
            cls._instance.console = Console(theme=custom_theme)
        return cls._instance

    def print_header(self, title: str) -> None:
        """Prints a styled header panel."""
        self.console.print(Panel(Text(title, justify="center", style="bold white"), style="blue"))

    def print_sub_header(self, title: str) -> None:
        """Prints a styled sub-header."""
        self.console.print(f"\n[bold underline]{title}[/bold underline]")

    def print_error(self, message: str) -> None:
        """Prints an error message."""
        self.console.print(f"[error]Error: {message}[/error]")

    def print_success(self, message: str) -> None:
        """Prints a success message."""
        self.console.print(f"[success]{message}[/success]")

    def print_info(self, message: str) -> None:
        """Prints an informational message."""
        self.console.print(f"[info]{message}[/info]")

    def print_warning(self, message: str) -> None:
        """Prints a warning message."""
        self.console.print(f"[warning]{message}[/warning]")

    def print_message(self, message: str) -> None:
        """Prints a standard message."""
        self.console.print(message)

    def print_panel(self, message: str, title: Optional[str] = None, style: str = "none") -> None:
        """Prints a message inside a panel."""
        self.console.print(Panel(message, title=title, style=style, expand=False))

    def print_banner(self, message: str, title: Optional[str] = None, style: str = "none") -> None:
        """Prints a full-width centered banner."""
        self.console.print(Panel(Text.from_markup(message, justify="center"), title=title, style=style, expand=True))

    def input(self, prompt: str) -> str:
        """
        Wrapper for input using rich console.
        Note: Rich console.input doesn't behave exactly like python input() in all cases,
        but allows for styled prompts.
        """
        return self.console.input(f"[bold medium_purple1]{prompt}[/bold medium_purple1]")

    def print_menu(self, title: str, options: List[str]) -> None:
        """
        Displays a menu list in a panel.
        """
        menu_text = "\n".join(options)
        self.console.print(Panel(menu_text, title=title, expand=False, style="blue", padding=(1, 2)))

    def print_table(self, title: str, columns: List[str], rows: List[List[str]]) -> None:
        """
        Displays data in a formatted table.
        """
        table = Table(title=title, show_header=True, header_style="bold magenta")
        
        for col in columns:
            table.add_column(col)
            
        for row in rows:
            table.add_row(*row)
            
        self.console.print(table)

# Global instance
console_manager = ConsoleManager()
