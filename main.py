# Program entry point
import subprocess
import sys
import os
import importlib.util

def install_dependencies():
    
    marker_file = ".dependencies_installed"
    req_file = "requirements.txt"
    
    # if os.path.exists(marker_file):
    #     return

    required_packages = []
    if os.path.exists(req_file):
        try:
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):


                        pkg_name = line.split('==')[0].split('>=')[0].split('<')[0].split('~=')[0].split('[')[0].strip()


                        required_packages.append(pkg_name)
        except Exception:
            pass

    missing_packages = []
    
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
            


    if not missing_packages:
        try:
            with open(marker_file, 'w') as f:
                f.write("Installed (Verified by import check)")
        except: 
            pass
        return

        

    if os.path.exists(req_file):
        try:
            with open(req_file, 'r') as f:
                packages_list = [line.strip() for line in f if line.strip()]
        except Exception:
            packages_list = ["(Unable to read requirements.txt)"]

        print("\n[FIRST RUN SETUP]")
        print("This application requires external libraries that appear to be missing:")
        for pkg in missing_packages:
            print(f" - {pkg}")
            
        print("\nWe can install all required packages for you automatically.")
        
        response = input("Would you like to install packages now? (y/n): ").strip().lower()
        
        if response == 'y':
            print("Installing dependencies... Please wait.")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "-r", req_file],
                    stdout=subprocess.DEVNULL
                )
                
                with open(marker_file, 'w') as f:
                    f.write("Installed")
                
                print("Installation successful! Starting application...\n")
            except subprocess.CalledProcessError:
                print("Error: Installation failed. Please check your internet connection or try running 'pip install -r requirements.txt' manually.\n")
        else:
            print("Skipping installation. Warning: The developers of this project HIGHLY RECOMMEND installing dependencies.\n")

install_dependencies()

from cli.session import Session
from cli.main_loop import run_program

from persistence.dao.user_manager import UserManager
from persistence.dao.camp_manager import CampManager
from persistence.dao.message_manager import MessageManager
from persistence.dao.announcement_manager import AnnouncementManager
from persistence.dao.system_notification_manager import SystemNotificationManager
from persistence.dao.audit_log_manager import AuditLogManager
from persistence.dao.camper_manager import CamperManager

from handlers.admin_handler import AdminHandler
from handlers.coordinator_handler import CoordinatorHandler
from handlers.leader_handler import LeaderHandler

from models.users import register_user_types
from handlers.base_handler import BaseHandler
from app_context import AppContext

register_user_types()

HANDLERS = {
    "Admin": AdminHandler,
    "Coordinator": CoordinatorHandler,
    "Leader": LeaderHandler,
}

def create_handler(user, context):
    """Create the appropriate handler based on user role."""
    handler_class = HANDLERS.get(user.role, BaseHandler)
    return handler_class(user, context)

def main():
    # Create managers ONCE (dependency injection)
    user_manager = UserManager()
    camp_manager = CampManager()
    message_manager = MessageManager()
    announcement_manager = AnnouncementManager()
    system_notification_manager = SystemNotificationManager()
    audit_log_manager = AuditLogManager()
    camper_manager = CamperManager()

    # Startup Banner
    from cli.startup_display import startup_display
    startup_display.display_welcome_banner()

    # Login
    session = Session()
    user = session.login()
    
    if user is None:
        return

    # Create Context
    context = AppContext(
        user_manager, 
        camp_manager, 
        message_manager, 
        announcement_manager, 
        system_notification_manager,
        audit_log_manager,
        camper_manager
    )

    # Create handler for this user's role
    handler = create_handler(user, context)

    # Run main loop with both user and handler
    run_program(user, handler)


if __name__ == "__main__":
    main()