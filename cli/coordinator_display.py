from .console_manager import console_manager
from rich.table import Table
from rich.panel import Panel

class CoordinatorDisplay:
    """
    Handles all UI display logic for Coordinator actions.
    Separates view concerns from CoordinatorHandler.
    """

    def display_camp_list(self, camps, title="Select Camp"):
        """
        Renders a list of camps in a styled Table (Design Option A).
        """
        table = Table(title=title, border_style="blue", header_style="bold medium_purple1")
        table.add_column("#", style="dim", width=4)
        table.add_column("Camp Name", style="bold white")
        table.add_column("Location")
        table.add_column("Initial Food", justify="right")
        table.add_column("Current Food", justify="right")
        table.add_column("Start Date")
        table.add_column("End Date")

        for i, camp in enumerate(camps, 1):
            current_stock = camp.current_food_stock
            current_color = "red" if camp.is_food_shortage() else "green"
            
            table.add_row(
                str(i),
                camp.name,
                camp.location,
                f"{camp.initial_food_stock} units",
                f"[{current_color}]{current_stock} units[/{current_color}]",
                str(camp.start_date),
                str(camp.end_date),
            )

        console_manager.console.print(table)
        console_manager.print_message("\n")


    def display_camp_creation_success(self, camp):
        """
        Renders a success panel with camp details (Design Option B - Summary Panel).
        """
        content = (
            f"[bold white]Camp Created Successfully![/bold white]\n\n"
            f"[bold]Name:[/bold] {camp.name}\n"
            f"[bold]Location:[/bold] {camp.location}\n"
            f"[bold]Dates:[/bold] {camp.start_date} to {camp.end_date}\n"
            f"[bold]Initial Food:[/bold] {camp.current_food_stock} units"
        )
        console_manager.print_panel(content, title="Success", style="bold medium_purple1")


    def display_payment_update_success(self, leader_name, old_rate, new_rate):
        """
        Renders a card showing the payment update (Design Option B - Leader Card).
        """
        content = (
            f"[bold white]User Updated: {leader_name}[/bold white]\n\n"
            f"Old Rate: £{old_rate}\n"
            f"[bold medium_purple1]New Rate: £{new_rate}[/bold medium_purple1]"
        )
        console_manager.print_panel(content, title="Payment Update", style="blue")


# Default instance
coordinator_display = CoordinatorDisplay()
