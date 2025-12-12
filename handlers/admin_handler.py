import uuid
import os
import json
from datetime import datetime
from handlers.base_handler import BaseHandler
from cli.input_utils import get_input, cancellable, wait_for_enter
from cli.console_manager import console_manager
from models.announcement import Announcement
from persistence.dao.system_notification_manager import SystemNotificationManager
from cli.view_admin import display_user_table
from services.weather_service import WeatherService
from rich.table import Table
from rich.console import Console



class AdminHandler(BaseHandler):
    """Handles Admin-specific actions."""
    def __init__(self, user, context):

        super().__init__(user, context)

        self.commands = self.parent_commands + [
            {"name": "Create User", "command": self.handle_create_user},
            {"name": "Delete User", "command": self.handle_delete_user},
            {"name": "Enable/Disable User", "command": self.handle_toggle_status},
            {"name": "Update User Info", "command": self.handle_update_user_info},
            {"name": "Post announcement", "command": self.post_announcement},
            {"name": "View Audit Logs", "command": self.view_audit_logs},
            {"name": "View Users", "command": self.view_users},
            {"name": "View Weather Forecast", "command": self.view_weather_forecast},
            {"name": "System Health Check", "command": self.handle_system_health_check},
            {"name": "Backup System Data", "command": self.handle_backup_data},
            {"name": "Restore System Data", "command": self.handle_restore_data},
        ]

        self.main_commands = self.commands.copy()

    def restore_main_commands(self):
        self.commands = self.main_commands


    def view_users(self):
        """Fetches all users from the user manager and displays them in a table."""
        console_manager.console.print("[bold medium_purple1]Fetching user data...[/bold medium_purple1]")
        
        user_list = self.context.user_manager.read_all()
        
        display_user_table(user_list)

        wait_for_enter()


    @cancellable 
    def handle_create_user(self):
        while True:
            username = get_input("Enter username (letters and numbers only) or 'b' to go back: ")
            if not username.strip():
                console_manager.print_error("Username cannot be empty.")
                continue
            if not username.isalnum():
                console_manager.print_error("Username must contain only letters and numbers.")
                continue
            
            if self.context.user_manager.find_user(username):
                console_manager.print_error(f"User '{username}' already exists. Please choose a different username.")
                continue
                
            break

        while True:
            password = get_input("Enter password: ")
            confirm_password = get_input("Confirm password: ")
            
            if password != confirm_password:
                console_manager.print_error("Passwords do not match. Please try again.")
                continue
            break
        
        # Role is restricted to Leader only
        role = "Leader"
        console_manager.print_info(f"Creating user with role: {role}")
        
        kwargs = {}
        try:
            rate_str = get_input("Enter daily payment rate: ")
            rate = float(rate_str)
            kwargs['daily_payment_rate'] = rate
        except ValueError:
            console_manager.print_warning("Invalid rate, defaulting to 0.0")
            kwargs['daily_payment_rate'] = 0.0

        success, message = self.context.user_manager.create_user(username, password, role=role, **kwargs)
        if success:
            console_manager.print_success(message)
            self.context.audit_log_manager.log_event(self.user.username, "Create User", f"Created user {username} as {role}")
            wait_for_enter()
        else:
            console_manager.print_error(message)
            wait_for_enter()


    @cancellable 
    def handle_delete_user(self):
        while True:
            username = self.get_username_with_search("Enter username to delete / 'b' to go back ")
            user = self.context.user_manager.find_user(username)
            if user:
                break
            console_manager.print_error(f"User '{username}' not found. Please try again.")

        camps = self.context.camp_manager.read_all()
        active_leadership = []
        for camp in camps:
            if camp.camp_leader == username and not camp.has_camp_finished():
                active_leadership.append(camp.name)
        
        if active_leadership:
            console_manager.print_error(f"Cannot delete user '{username}'. They are currently assigned as leader for active camps: {', '.join(active_leadership)}.")
            console_manager.print_info("Please reassign these camps before deleting the user.")
            wait_for_enter()
            return

        confirm = get_input(f"Are you sure you want to delete user '{username}'? (y/n): ")
        if confirm.lower() != 'y':
            console_manager.print_info("Deletion cancelled.")
            return

        success, message = self.context.user_manager.delete_user(username)
        if success:
            console_manager.print_success(message)
            self.context.audit_log_manager.log_event(self.user.username, "Delete User", f"Deleted user {username}")
            wait_for_enter()
        else:
            console_manager.print_error(message)
            wait_for_enter()

    @cancellable
    def handle_toggle_status(self):
        while True:
            username = self.get_username_with_search("Enter username or 'b' to go back")
            user = self.context.user_manager.find_user(username)
            if user:
                break
            console_manager.print_error(f"User '{username}' not found. Please try again.")
            
        if user['username'] == self.user.username:
            console_manager.print_error("You cannot disable your own account.")
            return

        current_status = user.get('enabled', True)
        status_str = "Enabled" if current_status else "Disabled"
        console_manager.print_info(f"Current status for {username}: {status_str}")
        
        if current_status:
            confirm = get_input("Disable user? (y/n): ")
            new_status = False if confirm.lower() == 'y' else True
        else:
            confirm = get_input("Enable user? (y/n): ")
            new_status = True if confirm.lower() == 'y' else False
            
        if new_status != current_status:
            success, message = self.context.user_manager.toggle_user_status(username, new_status)
            console_manager.print_success(message)
            self.context.audit_log_manager.log_event(self.user.username, "Toggle Status", f"Set {username} to {'Enabled' if new_status else 'Disabled'}")
        else:
            console_manager.print_info("No changes made.")
        
        wait_for_enter()

    @cancellable 
    def handle_update_user_info(self):
        console_manager.print_header("Update User Info")
        options = [
            "1. Update Password",
            "2. Update Daily Rate (Leader only)",
            "3. Change Username",
            "4. Change Role"
        ]
        console_manager.print_menu("Options", options)
        
        choice = get_input("Select option or 'b' to go back: ")
        
        if choice == '1':
            while True:
                username = self.get_username_with_search("Enter username")
                if self.context.user_manager.find_user(username):
                    break
                console_manager.print_error(f"User '{username}' not found. Please try again.")

            new_password = get_input("Enter new password: ")
            success, msg = self.context.user_manager.update_password(username, new_password)
            if success: 
                console_manager.print_success(msg)
                self.context.audit_log_manager.log_event(self.user.username, "Update Password", f"Updated password for {username}")
            else: console_manager.print_error(msg)
            wait_for_enter()
        elif choice == '2':
            while True:
                username = self.get_username_with_search("Enter username", role_filter="Leader")
                user = self.context.user_manager.find_user(username)
                if user:
                    break
                console_manager.print_error(f"User '{username}' not found. Please try again.")

            if user.get('role') != 'Leader':
                console_manager.print_error(f"User '{username}' is not a Leader.")
                wait_for_enter()
                return
                
            try:
                rate = float(get_input("Enter new daily rate: "))
                success, msg = self.context.user_manager.update_daily_payment_rate(username, rate)
                if success: 
                    console_manager.print_success(msg)
                    self.context.audit_log_manager.log_event(self.user.username, "Update Rate", f"Updated rate for {username} to {rate}")
                else: console_manager.print_error(msg)
            except ValueError:
                console_manager.print_error("Invalid rate.")
            wait_for_enter()
        elif choice == '3':
            while True:
                old_username = self.get_username_with_search("Enter current username")
                if self.context.user_manager.find_user(old_username):
                    break
                console_manager.print_error(f"User '{old_username}' not found. Please try again.")

            while True:
                new_username = get_input("Enter new username (letters and numbers only): ")
                if not new_username.strip():
                    console_manager.print_error("Username cannot be empty.")
                    continue
                if not new_username.isalnum():
                    console_manager.print_error("Username must contain only letters and numbers.")
                    continue
                break

            success, msg = self.context.user_manager.update_username(old_username, new_username)
            if success: 
                console_manager.print_success(msg)
                self.context.audit_log_manager.log_event(self.user.username, "Update Username", f"Changed {old_username} to {new_username}")
            else: console_manager.print_error(msg)
            wait_for_enter()
        elif choice == '4':
            while True:
                username = self.get_username_with_search("Enter username")
                if self.context.user_manager.find_user(username):
                    break
                console_manager.print_error(f"User '{username}' not found. Please try again.")

            new_role = get_input("Enter new role (Leader/Coordinator): ")
            success, msg = self.context.user_manager.update_role(username, new_role)
            if success: 
                console_manager.print_success(msg)
                self.context.audit_log_manager.log_event(self.user.username, "Update Role", f"Changed {username} role to {new_role}")
            else: console_manager.print_error(msg)
            wait_for_enter()
        else:
            console_manager.print_error("Invalid selection")
            wait_for_enter()

    @cancellable
    def post_announcement(self):
        """Post a new global announcement."""
        console_manager.print_info("Posting new announcement (visible to all users).")
        content = get_input("Enter content or 'b' to go back: ")
        
        announcement = Announcement(
            announcement_id=str(uuid.uuid4()),
            author=self.user.username,
            content=content
        )
        
        try:
            if self.context.announcement_manager:
                self.context.announcement_manager.add(announcement.to_dict())
                console_manager.print_success("Announcement posted successfully.")
                self.context.audit_log_manager.log_event(self.user.username, "Post Announcement", f"Content: {content[:20]}...")
            else:
                console_manager.print_error("Error: Announcement manager not initialized.")
        except Exception as e:
            console_manager.print_error(f"Error posting announcement: {e}")

    @cancellable
    def view_audit_logs(self):
        logs = self.context.audit_log_manager.read_all()
        if not logs:
            console_manager.print_info("No audit logs found.")
            return

        # Sort by timestamp descending
        logs.sort(key=lambda x: x['timestamp'], reverse=True)

        columns = ["Timestamp", "User", "Action", "Details"]
        rows = []
        for log in logs:
            rows.append([
                log.get("timestamp", ""),
                log.get("username", ""),
                log.get("action", ""),
                log.get("details", "")
            ])
        
        console_manager.print_table("System Audit Logs", columns, rows)
        wait_for_enter()
    
    @cancellable
    def view_weather_forecast(self):
        camps = self.context.camp_manager.read_all()

        if not camps:
            console_manager.print_error("No camps available.")
            return
        
        self.display.display_camp_list(camps)

        while True:
            choice = get_input("Select camp number: ")
            if not choice.isdigit(): continue
            idx = int(choice) - 1
            if 0 <= idx < len(camps):
                camp = camps[idx]
                break

        console = Console()
        with console.status("[bold green]Fetching live weather data, Please wait...[/]"):
            ws = WeatherService()
            df_forecast, error = ws.get_weekly_forecast(camp.location)

        if error:
            console_manager.print_error(f"Weather Unavailable: {error}")
            wait_for_enter()
            return
        
        if df_forecast is None or df_forecast.empty:
            console_manager.print_error("No weather data returned. Inconvenience is deeply regretted.")
            wait_for_enter()
            return
        
        table = Table(title=f"7-Day Forecast for {camp.location}")
        table.add_column("Date")
        table.add_column("Condition")


        for index, row in df_forecast.iterrows():
            status = row['status']
            color = "green" if status == "Good" else ("yellow" if status == "Rainy" else "red")
            table.add_row(str(row['date']), f"[{color}]{status}[/]")


        console_manager.console.print(table)


    def handle_system_health_check(self):
        """Performs a comprehensive system health check and displays a dashboard."""
        import os
        from rich.panel import Panel
        from rich.columns import Columns
        from rich.align import Align
        from rich.table import Table

        console_manager.print_info("Running System Health Check...")
        
        camps = self.context.camp_manager.read_all()
        users = self.context.user_manager.read_all()
        user_map = {u['username']: u for u in users}
        
        issues = []
        food_shortages = []
        missing_contacts = []
        medical_cases = 0
        total_campers = 0
        total_projected_cost = 0.0
        total_activities = 0
        total_camp_days = 0
        
        for camp in camps:
            if camp.camp_leader:
                if camp.camp_leader not in user_map:
                    issues.append(f"[Camp: {camp.name}] Leader '{camp.camp_leader}' does not exist.")
                else:
                    leader_data = user_map[camp.camp_leader]
                    if leader_data.get('role') != "Leader":
                        issues.append(f"[Camp: {camp.name}] Assigned leader '{camp.camp_leader}' has role '{leader_data.get('role')}', expected 'Leader'.")
                    
                    # Financials (Projected Cost)
                    rate = leader_data.get('daily_payment_rate', 0.0)
                    duration = (camp.end_date - camp.start_date).days + 1
                    total_projected_cost += (rate * duration)
            else:
                issues.append(f"[Camp: {camp.name}] No leader assigned.")
                
            if camp.start_date > camp.end_date:
                issues.append(f"[Camp: {camp.name}] Invalid dates: Start ({camp.start_date}) > End ({camp.end_date}).")
                
            if camp.is_food_shortage():
                food_shortages.append(camp.name)
            
            # 4. Campers & Safety
            for camper in camp.campers:
                total_campers += 1
                if camper.medical_info:
                    medical_cases += 1
                if not camper.contact:
                    missing_contacts.append(f"{camper.name} (in {camp.name})")
            
            # 5. Activities
            total_activities += len(camp.activities)
            total_camp_days += (camp.end_date - camp.start_date).days + 1

        # --- Storage Stats ---
        storage_stats = []
        # Safely access filepaths if they exist on the managers
        managers_to_check = [
            ("Users", getattr(self.context.user_manager, 'filepath', None)),
            ("Camps", getattr(self.context.camp_manager, 'filepath', None))
        ]
        
        for name, path in managers_to_check:
            if path and os.path.exists(path):
                try:
                    size_kb = os.path.getsize(path) / 1024
                    storage_stats.append(f"{name}: {size_kb:.2f} KB")
                except Exception:
                    storage_stats.append(f"{name}: Error")
            else:
                storage_stats.append(f"{name}: N/A")

        # --- Display Construction ---
        
        # 1. Critical Alerts Panel
        alerts = []
        if food_shortages:
            alerts.append(f"[bold red]! Food Shortage in {len(food_shortages)} camps[/bold red]")
        if missing_contacts:
            alerts.append(f"[bold red]! {len(missing_contacts)} campers missing emergency contact[/bold red]")
        if issues:
            alerts.append(f"[bold red]! {len(issues)} integrity issues detected[/bold red]")
            
        if not alerts:
            alert_panel = Panel("[bold green]No Critical Alerts[/bold green]", title="[bold red]Critical Alerts[/bold red]", border_style="green")
        else:
            alert_panel = Panel("\n".join(alerts), title="[bold red]Critical Alerts[/bold red]", border_style="red")

        # 2. Operational Stats Table
        stats_table = Table(show_header=False, box=None, padding=(0, 2))
        stats_table.add_row("Total Users", str(len(users)))
        stats_table.add_row("Total Camps", str(len(camps)))
        stats_table.add_row("Total Campers", str(total_campers))
        stats_table.add_row("Medical Cases", f"[yellow]{medical_cases}[/yellow]")
        stats_table.add_row("Avg Activities/Day", f"{total_activities/total_camp_days:.2f}" if total_camp_days > 0 else "0")
        
        stats_panel = Panel(stats_table, title="[bold blue]Operational Stats[/bold blue]", border_style="blue")

        # 3. Financial & System Panel
        fin_table = Table(show_header=False, box=None, padding=(0, 2))
        fin_table.add_row("Projected Staff Cost", f"[bold green]${total_projected_cost:,.2f}[/bold green]")
        fin_table.add_row("Storage Usage", "\n".join(storage_stats))
        
        fin_panel = Panel(fin_table, title="[bold magenta]Financial & System[/bold magenta]", border_style="magenta")

        # Render Dashboard
        console_manager.console.print("\n")
        console_manager.console.print(Align.center("[bold underline]System Health Dashboard[/bold underline]"))
        console_manager.console.print(alert_panel)
        console_manager.console.print(Columns([stats_panel, fin_panel]))
        
        if food_shortages:
            console_manager.console.print("\n[bold red]Camps with Food Shortage:[/bold red]")
            for name in food_shortages:
                console_manager.console.print(f"- {name}")

        if missing_contacts:
             console_manager.console.print("\n[bold red]Missing Emergency Contacts:[/bold red]")
             for c in missing_contacts:
                 console_manager.console.print(f"- {c}")

        if issues:
            console_manager.console.print("\n[bold red]Integrity Issues Details:[/bold red]")
            for issue in issues:
                console_manager.console.print(f"- {issue}")
        
        if not issues and not food_shortages and not missing_contacts:
            console_manager.print_success("\nSystem is running smoothly.")

        wait_for_enter()

    @cancellable
    def handle_backup_data(self):
        """Backs up all system data to a JSON file."""
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.json"
        filepath = os.path.join(backup_dir, filename)
        
        console_manager.print_info(f"Creating backup: {filename}...")
        
        try:
            # Gather data
            # Note: CampManager returns objects, need to convert to dicts
            camps_data = [c.to_dict() for c in self.context.camp_manager.read_all()]
            
            backup_data = {
                "timestamp": timestamp,
                "users": self.context.user_manager.read_all(),
                "camps": camps_data,
                "messages": self.context.message_manager.read_all(),
                "announcements": self.context.announcement_manager.read_all(),
                "notifications": self.context.system_notification_manager.read_all(),
                "audit_logs": self.context.audit_log_manager.read_all()
            }
            
            with open(filepath, "w") as f:
                json.dump(backup_data, f, indent=4)
                
            console_manager.print_success(f"Backup created successfully at {filepath}")
            self.context.audit_log_manager.log_event(self.user.username, "System Backup", f"Created backup {filename}")
            
        except Exception as e:
            console_manager.print_error(f"Backup failed: {e}")
            
        wait_for_enter()

    @cancellable
    def handle_restore_data(self):
        """Restores system data from a backup file."""
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            console_manager.print_error("No backups directory found.")
            wait_for_enter()
            return
            
        files = [f for f in os.listdir(backup_dir) if f.endswith(".json")]
        if not files:
            console_manager.print_error("No backup files found.")
            wait_for_enter()
            return
            
        files.sort(reverse=True) # Newest first
        
        console_manager.print_info("Available Backups:")
        for i, f in enumerate(files, 1):
            print(f"{i}. {f}")
            
        choice = get_input("Select backup to restore (number) or 'b' to go back: ")
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(files):
                console_manager.print_error("Invalid selection.")
                return
            selected_file = files[idx]
        except ValueError:
            console_manager.print_error("Invalid input.")
            return
            
        confirm = get_input(f"WARNING: This will OVERWRITE all current system data with data from {selected_file}.\nType 'CONFIRM' to proceed: ")
        if confirm != "CONFIRM":
            console_manager.print_info("Restore cancelled.")
            return
            
        filepath = os.path.join(backup_dir, selected_file)
        console_manager.print_info(f"Restoring from {selected_file}...")
        
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                
            # Restore Users
            # UserManager caches data in memory, so we update memory and save
            if "users" in data:
                self.context.user_manager.users = data["users"]
                self.context.user_manager.save_data()
                print("✓ Users restored")
                
            # Restore Camps
            if "camps" in data:
                with open(self.context.camp_manager.filepath, "w") as f:
                    json.dump(data["camps"], f, indent=4)
                print("✓ Camps restored")
                
            # Restore Messages
            if "messages" in data:
                with open(self.context.message_manager.filepath, "w") as f:
                    json.dump(data["messages"], f, indent=4)
                print("✓ Messages restored")
                
            # Restore Announcements
            if "announcements" in data:
                # AnnouncementManager uses 'data_file'
                with open(self.context.announcement_manager.data_file, "w") as f:
                    json.dump(data["announcements"], f, indent=4)
                print("✓ Announcements restored")
                
            # Restore Notifications
            if "notifications" in data:
                # SystemNotificationManager uses 'file_path'
                with open(self.context.system_notification_manager.file_path, "w") as f:
                    json.dump(data["notifications"], f, indent=4)
                print("✓ Notifications restored")
                
            # Restore Audit Logs
            if "audit_logs" in data:
                with open(self.context.audit_log_manager.filepath, "w") as f:
                    json.dump(data["audit_logs"], f, indent=4)
                print("✓ Audit Logs restored")
                
            console_manager.print_success("System restore completed successfully.")
            self.context.audit_log_manager.log_event(self.user.username, "System Restore", f"Restored from {selected_file}")
            
        except Exception as e:
            console_manager.print_error(f"Restore failed: {e}")
            import traceback
            traceback.print_exc()
            
        wait_for_enter()