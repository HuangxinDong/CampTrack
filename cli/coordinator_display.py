from .console_manager import console_manager
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.columns import Columns
from rich.align import Align
from rich.text import Text
from rich.console import Group

class CoordinatorDisplay:
    """
    Handles all UI display logic for Coordinator actions.
    Separates view concerns from CoordinatorHandler.
    """
    
    # Constants for Dashboard Styling (Phase 9D)
    PINK = "#FF69B4"
    BAR_COLOR = "cyan"
    GOOD_COLOR = "bright_green"
    BAD_COLOR = "red"

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
             # Ensure dates are strings for display
            start_str = camp.start_date.strftime('%Y-%m-%d') if hasattr(camp.start_date, 'strftime') else str(camp.start_date)
            end_str = camp.end_date.strftime('%Y-%m-%d') if hasattr(camp.end_date, 'strftime') else str(camp.end_date)
            
            table.add_row(
                str(i),
                f"[bold]{camp.name}[/bold]",
                camp.location,
                str(camp.initial_food_stock),
                str(camp.current_food_stock),
                start_str,
                end_str
            )

        console_manager.console.print(table)

    def display_camp_details(self, camp):
        """
        Displays detailed information card for a single camp.
        """
        title = f"[bold {self.PINK}]Camp Details: {camp.name}[/]"
        
        # Leader formatting
        leader_display = camp.camp_leader if camp.camp_leader else "[italic dim]Unassigned[/]"
        
        content = (
            f"[bold]Location:[/bold] {camp.location}\n"
            f"[bold]Leader:[/bold] {leader_display}\n"
            f"[bold]Dates:[/bold] {camp.start_date} to {camp.end_date}\n"
            f"[bold]Food Stock:[/bold] {camp.current_food_stock} / {camp.initial_food_stock}\n"
            f"[bold]Campers:[/bold] {len(camp.campers)}"
        )
        
        console_manager.print_panel(content, title=title, style="white")

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


    def display_payment_update(self, camp_name, new_rate):
        content = (
            f"Successfully updated payment rate for [bold white]{camp_name}[/bold white].\n"
            f"[bold medium_purple1]New Rate: £{new_rate}[/bold medium_purple1]"
        )
        console_manager.print_panel(content, title="Payment Update", style="blue")

    def display_full_dashboard(self, overview_data, engagement_metrics=None):
        """
        Renders the Full Coordinator Dashboard (Design 9 - Hybrid Quad Chart).
        """
        aggregates = overview_data.get('aggregates', {})
        details = overview_data.get('details', [])

        if not details:
            console_manager.print_error("No camps to display.")
            return
            
        console_manager.console.print(self._make_header("SUMMARYDASHBOARD"))
        
        # 1. KPI Row (Top)
        kpis = self._render_kpi_row(aggregates)
        
        # 2. Quad Charts (Middle)
        quads = self._render_quad_charts(details, engagement_metrics or {})
        
        # 3. Footer Summary (Bottom)
        footer = self._render_summary_footer(aggregates)

        # Print all as a unified view
        console_manager.console.print(Group(
            kpis,
            Text("\n"),
            quads,
            Text("\n"),
            footer
        ))

    # --- Private Helpers for Design 9 ---

    def _make_header(self, title):
        return Panel(
            Align.center(f"[bold white]{title}[/]", vertical="middle"),
            style=f"bold {self.PINK}",
            border_style=self.PINK,
            height=3
        )

    def _render_kpi_row(self, aggs):
        """Renders the top row of KPI tiles."""
        
        # KPI 1: Population
        kpi_pop = Panel(
            Align.center(f"[bold white font=40]{aggs.get('total_campers', 0)}[/]\n[dim]Total Campers[/]"),
            title="[bold white]POPULATION[/]", border_style=self.PINK, height=5
        )
        
        # KPI 2: Allocation Coverage
        total_camps = aggs.get('total_camps', 1)
        assigned = aggs.get('assigned_leaders', 0)
        pct = int((assigned / total_camps) * 100) if total_camps > 0 else 0
        
        kpi_alloc = Panel(
            Align.center(f"[bold white font=40]{pct}%[/]\n[dim]Leader Coverage[/]"),
            title="[bold white]ALLOCATION[/]", border_style=self.PINK, height=5
        )
        
        # KPI 3: Safety (Dynamic Style)
        alerts = aggs.get('shortage_camps', 0)
        if alerts > 0:
            border = self.BAD_COLOR
            text = f"[bold {self.BAD_COLOR} font=40]{alerts}[/] [bold white]/ {total_camps}[/]\n[bold {self.BAD_COLOR}]Active Alerts[/]"
        else:
            border = "dim white" # Grey/Neutral
            text = f"[dim white font=40]0[/] [dim]/ {total_camps}[/]\n[dim]No Active Alerts[/]"
            
        kpi_safe = Panel(
            Align.center(text),
            title="[bold white]NOTIFICATIONS[/]", border_style=border, height=5
        )
        
        return Columns([kpi_pop, kpi_alloc, kpi_safe], expand=True)

    def _render_quad_charts(self, details, metrics):
        """Renders the 2x2 Matrix of Charts."""
        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        
        # 1. Camper Distribution
        t_camp = Table(box=box.SIMPLE, show_header=False, expand=True)
        t_camp.add_column("N", style="bold white")
        t_camp.add_column("B")
        t_camp.add_column("V", justify="right", style="bold white")
        
        total_pop = sum(d['campers_count'] for d in details) or 1
        
        for row in details:
            count = row['campers_count']
            bar_len = int((count / total_pop) * 20)
            bar = "█" * bar_len
            t_camp.add_row(row['name'], f"[{self.BAR_COLOR}]{bar}[/]", str(count))
            
        p_camp = Panel(t_camp, title="[bold white]CAMPER DISTRIBUTION[/]", border_style=self.PINK, height=9)

        # 2. Global Engagement
        t_act = Table(box=box.SIMPLE, show_header=False, expand=True)
        t_act.add_column("N", style="bold white")
        t_act.add_column("B")
        t_act.add_column("V", justify="right", style="bold white")
        
        for act, rate in metrics.items():
            bar_len = int(rate * 15)
            bar = "█" * bar_len
            t_act.add_row(act, f"[{self.BAR_COLOR}]{bar}[/]", f"{int(rate*100)}%")
            
        p_act = Panel(t_act, title="[bold white]ACTIVITY ENGAGEMENT[/]", border_style=self.PINK, height=9)

        # 3. Leader Allocation Map
        t_lead = Table(box=box.SIMPLE, show_header=False, expand=True)
        t_lead.add_column("N", style="bold white")
        t_lead.add_column("S")
        
        for row in details:
            leader = row['leader']
            if leader and leader != '[Unassigned]':
                status = f"[{self.GOOD_COLOR}]● ASSIGNED ({leader})[/]"
            else:
                status = f"[bold {self.BAD_COLOR}]✖ UNASSIGNED[/]"
            t_lead.add_row(row['name'], status)
            
        p_lead = Panel(t_lead, title="[bold white]LEADER ALLOCATION[/]", border_style=self.PINK, height=9)

        # 4. Food Stock Levels
        t_food = Table(box=box.SIMPLE, show_header=False, expand=True)
        t_food.add_column("N", style="bold white")
        t_food.add_column("B")
        t_food.add_column("V", justify="right", style="bold white")
        
        # Find max stock for scaling (avoid massive bars if one camp has 1000)
        max_stock = max((d['food_stock'] for d in details), default=100) or 1
        
        for row in details:
            stock = row['food_stock']
            color = self.GOOD_COLOR if stock >= 10 else self.BAD_COLOR
            bar_len = int((stock / max_stock) * 15)
            bar = "█" * bar_len
            t_food.add_row(row['name'], f"[{color}]{bar}[/]", str(stock))
            
        p_food = Panel(t_food, title="[bold white]FOOD STOCK LEVELS[/]", border_style=self.PINK, height=9)

        # Layout Logic
        grid.add_row(p_camp, p_act)
        grid.add_row(p_lead, p_food) # Removed spacer row for cleaner look with panel borders
        return grid

    def _render_summary_footer(self, aggs):
        """Renders the interpretation footer."""
        alerts = aggs.get('shortage_camps', 0)
        total_camps = aggs.get('total_camps', 1)
        healthy = total_camps - alerts
        
        if alerts > 0:
            status_text = f"[bold {self.BAD_COLOR}]{alerts} Critical Alerts[/]"
            dist_status = "Attention Needed: Low stock detected in some camps."
        else:
             status_text = f"[bold {self.GOOD_COLOR}]All Systems Healthy[/]"
             dist_status = "Optimal: All camps possess sufficient resources."

        summary_text = (
            f"Food Stock Summary: [bold {self.BAR_COLOR}]{aggs.get('total_food', 0)} units[/] across {total_camps} camps.\n"
            f"Health: [bold {self.GOOD_COLOR}]{healthy} Balanced[/], {status_text}\n"
            f"[italic]{dist_status}[/]"
        )
        return Panel(summary_text, title="[bold white]INVENTORY SNAPSHOT[/]", border_style=self.PINK)


# Default instance
coordinator_display = CoordinatorDisplay()
