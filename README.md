# Scout Camp Management System

A CLI-based management system for Scout Camps. Developed for COMP0066 Course Project.

## Features

### Access Control
*   **Admin**: System-wide configuration, user management, system health monitoring, data backup/restore, and audit logging.
*   **Camp Leader**: Camp-specific management including camper CSV imports, resource tracking, and emergency contact lookup.
*   **Coordinator**: Multi-camp oversight and logistics planning.

### Functionality
*   **Global Search**: Integrated search for campers, activities, and messages (hotkey: `s`).
*   **Data Integrity**: Conflict detection for scheduling and camper registration.
*   **Communication**: Internal messaging and system-wide announcements.
*   **Persistence**: JSON-based storage with automated backup capabilities.

## Setup

Requires Python 3.8+.

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Launch application:
    ```bash
    python main.py
    ```

## Controls

*   `b`: Back / Cancel
*   `q`: Quit
*   `s`: Global Search (Main Menu)

## Architecture

*   `handlers/`: Role-specific business logic.
*   `models/`: Domain entities.
*   `persistence/`: Data access layer (DAO) and JSON storage.
*   `cli/`: Terminal interface components.
*   `backups/`: System snapshots.

