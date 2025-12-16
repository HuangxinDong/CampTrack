from rich.table import Table
from rich.panel import Panel
from .console_manager import console_manager

class LeaderDisplay:
    """
    Handles all UI display logic for Leader actions.
    Separates view concerns from LeaderHandler.
    """

    def _activity_snapshot(self, activity):
        """Return dict view for Activity objects or pass-through for dicts."""
        return activity.to_dict() if hasattr(activity, "to_dict") else activity

    def display_error(self, message):
        console_manager.print_error(message)

    def display_warning(self, message):
        console_manager.print_warning(message)

    def display_success(self, message):
        console_manager.print_success(message)

    def display_info(self, message):
        console_manager.print_info(message)

    def display_camp_selection(self, camps, user_username):
        """
        Renders the list of camps for supervision selection.
        """
        console_manager.print_panel("Select a Camp to Supervise", style="cyan")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Camp Name")
        table.add_column("Location")
        table.add_column("Dates")
        table.add_column("Current Leader")
        table.add_column("Status")

        for i, camp in enumerate(camps, 1):
            leader = camp.camp_leader
            if not leader:
                leader_display = "[dim]None[/dim]"
                status = "[green]Available[/green]"
            elif leader == user_username:
                leader_display = "[bold green]You[/bold green]"
                status = "[blue]Already Supervising[/blue]"
            else:
                leader_display = f"[red]{leader}[/red]"
                status = "[red]Taken[/red]"
            
            dates = f"{camp.start_date} to {camp.end_date}"
            table.add_row(str(i), camp.name, camp.location, dates, leader_display, status)

        console_manager.console.print(table)

    def display_camp_food_update(self, camp, total_required, num_campers, days, new_food):
        """
        Displays summary after updating food settings.
        """
        console_manager.console.print(
            f"\n[bold]Total Food Required for {camp.name}:[/bold] {total_required} units\n"
            f"  ({num_campers} campers x {days} days x {new_food} food)"
        )

    def display_camper_csv_list(self, csv_files):
        """
        Lists available CSV files for import.
        """
        console_manager.print_panel("Available Camper CSV Files", style="cyan")
        for i, f in enumerate(csv_files, 1):
            console_manager.console.print(f"{i}. {f}")

    def display_campers(self, camp):
        """
        Displays a list of campers in a camp.
        """
        table_lines = [f"[bold]{camp.name} Campers[/bold]"]
        table_lines.append("─" * 40)

        if not camp.campers:
            table_lines.append("No campers yet.")
        else:
            for c in camp.campers:
                table_lines.append(f"{c.name} (Age {c.age}) — {c.contact}")

        console_manager.print_panel("\n".join(table_lines), style="cyan")

    def display_camper_search_results(self, found_campers):
        """
        Displays search results for campers.
        found_campers: list of tuples (camp_name, camper_obj)
        """
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Camp")
        table.add_column("Name")
        table.add_column("Contact")
        
        for i, (camp_name, camper) in enumerate(found_campers, 1):
            table.add_row(str(i), camp_name, camper.name, camper.contact)
            
        console_manager.console.print(table)
        console_manager.console.print("[dim]Enter number to view Emergency/Medical Info, 's' to search again, or 'b' to back[/dim]")

    def display_emergency_details(self, camper, camp_name):
        """
        Displays emergency details for a specific camper.
        """
        console_manager.print_panel(f"""
[bold]Emergency Details[/bold]
[green]Name:[/green] {camper.name}
[green]Camp:[/green] {camp_name}
[green]Age:[/green] {camper.age}
[green]Contact:[/green] {camper.contact}
[yellow]Medical Info:[/yellow] {camper.medical_info or 'None'}
""", style="red")

    def display_daily_reports_menu(self):
        """
        Displays the daily reports menu.
        """
        console_manager.print_panel("""
[bold]Daily Reports[/bold]
1. Create New Report
2. View Reports
3. Delete Report
""", style="blue")

    def display_daily_reports_list(self, reports):
        """
        Displays a table of daily reports.
        """
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Date", width=12)
        table.add_column("Summary", width=40)
        table.add_column("Activities")
        table.add_column("Injuries")
        table.add_column("Achievements")

        for r in reports:
            injuries = str(r.get("injured_count", 0)) if r.get("injury") else "0"
            table.add_row(
                r["date"],
                r["text"][:40] + "",
                ", ".join(r.get("activities", [])),
                injuries,
                ", ".join(r.get("achievements", [])),
            )

        console_manager.console.print(table)

    def display_reports_for_deletion(self, reports):
        """
        Displays reports as a simple list for deletion selection.
        """
        console_manager.print_panel("Reports:", style="blue")
        for i, r in enumerate(reports, 1):
            console_manager.console.print(f"{i}. {r['date']} — {r['text'][:40]}")

    def display_statistics(self, statistics_data, total_earnings):
        """
        Displays the statistics table and total earnings.
        statistics_data: list of dicts containing row data
        """
        console_manager.print_panel("Statistics for Your Camps", style="cyan")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Camp")
        table.add_column("Campers", justify="center")
        table.add_column("Avg Participation Rate", justify="center")
        table.add_column("Food Used", justify="center")
        table.add_column("Incidents", justify="center")
        table.add_column("Activities", justify="center")
        table.add_column("Achievements", justify="center")
        table.add_column("Earnings", justify="center")

        for row in statistics_data:
            table.add_row(
                row["camp_name"],
                row["campers"],
                row["participation"],
                row["food_used"],
                row["incidents"],
                row["activities"],
                row["achievements"],
                row["earnings"],
            )

        console_manager.console.print(table)

        console_manager.print_panel(
            f"[bold green]Total Earnings Across All Camps: £{total_earnings}[/bold green]",
            style="green"
        )

    def display_camp_selection_simple(self, camps):
        """
        Simple list for selecting a camp to perform actions on.
        """
        console_manager.print_panel("Select Camp", style="cyan")
        for i, c in enumerate(camps, 1):
            status = c.get_schedule_status()
            console_manager.console.print(f"{i}. {c.name} ({status}) ({c.location})")

    def display_activities_menu(self):
        """
        Displays the activities management menu.
        """
        console_manager.print_panel("""
[bold]Activity Management[/bold]
1. Add Activities to Camp
2. View Camp Activities
3. Add New Activity to Library
4. Search Activity Library
5. Assign Campers to Activities
6. Remove Activity
""", style="blue")

    def display_search_activity_results(self, matches):
        """
        Displays results from searching the activity library.
        """
        console_manager.print_panel(f"Found {len(matches)} activities:", style="blue")
        for a in matches:
            console_manager.console.print(f"• {a}")

    def display_camp_activities(self, camp):
        """
        Displays activities currently assigned to a camp.
        """
        lines = [f"[bold]{camp.name} Activities[/bold]", "─" * 40]

        snapshots = [self._activity_snapshot(a) for a in camp.activities]
        sorted_activities = sorted(snapshots, key=lambda x: (x.get("date",""), x.get("session","")))

        for activity in sorted_activities:
            name = activity.get("name", "Unknown")
            date_str = activity.get("date", "Unknown Date")
            session = activity.get("session", "Unknown Session")
            is_indoor = activity.get("is_indoor", False)
            location_type = "Indoor" if is_indoor else "Outdoor"
            camper_count = len(activity.get("camper_ids", []))
            
            lines.append(f"• [bold]{date_str}[/bold] | [cyan]{session}[/cyan] | {name} ({location_type}) — {camper_count} campers")

        console_manager.print_panel("\n".join(lines), style="blue")

    def display_activity_library(self, library):
        """
        Displays the current activity library.
        """
        console_manager.print_panel("Current Activity Library", style="blue")
        if library:
            # library is a dict now
            for i, (name, meta) in enumerate(library.items(), 1):
                is_indoor = meta.get("is_indoor", False)
                loc = "Indoor" if is_indoor else "Outdoor"
                console_manager.console.print(f"{i}. {name} [dim]({loc})[/dim]")
        else:
            console_manager.console.print("[dim]No activities yet.[/dim]")

    def display_added_activities(self, added, camp, camper_names, camper_count):
        """
        Displays success message for added activities.
        """
        console_manager.print_success(
            f"Added {', '.join(added)} to {camp.name}. "
            f"All {camper_count} campers ({camper_names}) assigned."
        )

    def select_csv_file(self, csv_files):
        """
        Displays available CSV files and gets user selection.
        Returns the selected filename or None if cancelled/invalid.
        Replaces 'display_camper_csv_list' and manual input loop in handler.
        """
        if not csv_files:
            console_manager.print_error("No CSV files found.")
            return None

        console_manager.print_panel("Available Camper CSV Files", style="cyan")
        for i, f in enumerate(csv_files, 1):
            console_manager.console.print(f"{i}. {f}")
        
        from cli.input_utils import get_input # Lazy import to avoid circular dep if any
        choice = get_input("Choose CSV file number: ")

        try:
            return csv_files[int(choice) - 1]
        except:
            console_manager.print_error("Invalid selection.")
            return None

    def display_import_results(self, results, camp_name):
        """
        Displays the results of a CSV import operation.
        """
        imported = results["imported_count"]
        skipped = results["skipped_count"]
        errors = results["errors"]
        warnings = results["warnings"]

        if warnings:
            for w in warnings:
                console_manager.print_warning(w)

        if errors:
            for e in errors:
                console_manager.print_error(e)

        console_manager.print_success(f"Imported {imported} campers into {camp_name}. (Skipped {skipped} conflicts)")
        from cli.input_utils import wait_for_enter
        wait_for_enter()

    def display_conflict_resolution(self, existing, new_name):
        """
        Displays a conflict resolution screen comparing existing and new activities.
        """
        snap = self._activity_snapshot(existing)
        existing_name = snap.get("name", "Unknown")
        existing_count = len(snap.get("camper_ids", []))
        
        console_manager.print_panel(f"""
[bold red]Time Slot Conflict Detected[/bold red]

[bold]EXISTING Activity:[/bold] {existing_name}
[dim]• Campers Assigned: {existing_count}[/dim]

[bold]NEW Activity:[/bold]      {new_name}
[dim]• Replaces the existing activity and clears the roster.[/dim]
""", style="red")

    def display_weekly_schedule(self, camp):
        """
        Renders a weekly schedule using the 'Neon Timeline' style (Option 10).
        """
        dates = sorted(list(set(camp.get_date_range())))
        sessions = ["Morning", "Afternoon", "Evening"]
        primary_pink = "#FF69B4"

        console_manager.print_panel(f"Weekly Schedule: {camp.name}", style=primary_pink)

        # Organize activities by date and session
        schedule = {d: {s: None for s in sessions} for d in dates}
        for act in camp.activities:
            snap = self._activity_snapshot(act)
            d = snap.get("date")
            s = snap.get("session")
            if d in schedule and s in sessions:
                schedule[d][s] = snap

        table = Table.grid(padding=(0, 1))
        table.add_column("Marker", justify="center", width=4)
        table.add_column("Content")

        for d in dates:
            # Day Header
            table.add_row(f"[bold {primary_pink}]●[/]", f"[bold underline white]{d}[/]")
            
            for s in sessions:
                act = schedule[d][s]
                line = f"[bold {primary_pink}]│[/]"
                
                if act:
                    name = act.get("name")
                    count = len(act.get("camper_ids", []))
                    row_content = f"[bold white]{s}:[/]  [bold {primary_pink}]{name}[/] ({count} campers)"
                else:
                    row_content = f"[dim italic]{s}:  No activity scheduled for this session[/dim italic]"
                
                table.add_row(line, row_content)
            
            # Spacer between days
            table.add_row(f"[bold {primary_pink}]│[/]", "") 

        console_manager.console.print(table)
        console_manager.console.print("")

    def confirm_activity_removal(self, activity):
        """
        Displays confirmation for activity removal.
        """
        snap = self._activity_snapshot(activity)
        name = snap.get("name")
        count = len(snap.get("camper_ids", []))
        console_manager.print_warning(f"Are you sure you want to remove '{name}'? ({count} campers assigned)")

# Default instance
leader_display = LeaderDisplay()
