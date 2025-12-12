# Scout Camp Management System

A CLI-based management system for Scout Camps. Developed for COMP0066 Course Project.

In addition to meeting all the requirements of the coursework brief, we also implemented:

## Core Functionality

### Administrator
*  **System Health Overview**: Displays key indicators related to data integrity and resource status.
*   **Backup & Restore**: JSON-based full system snapshot and restoration.
*   **Audit Log**: Records critical administrative actions.
*   **User Protection Rules**: Prevents deletion of active leaders.

### Coordinator
*   **Schedule Conflict Detection**: Automated identification of leader schedule overlaps.
*   **Visual Analytics**: Terminal-based charting for food stocks and demographics.
*   **Camp Overview**: Provides aggregated information across camps.

### Camp Leader
*   **Bulk Camper Import**: Bulk CSV camper registration with cross-camp conflict validation.
*   **Activity Scheduling**: Scheduling system with rule enforcement (max 2/day) and slot collision handling.
*   **Emergency Information Lookup**: Quick access to camper contact and medical details.
*   **Daily Reports**: Keyword extraction for daily activity summaries.

## Features

*   **Search Helper**: Type `s` at any selection prompt to search.
*   **Internal Messaging**: Internal messaging system and global announcements.
*   **Persistence**: JSON-based storage with automated backup capabilities.
*   **Authentication**: Role-based login with password confirmation and uniqueness checks.
*   **Weather Integration**: Real-time forecasting via Open-Meteo API for safe activity planning.
*   **Auto-Provisioning**: Automatic verification and installation of system dependencies on startup.



## Controls

*   `b`: Back / Cancel
*   `q`: Quit
*   `s`: Search (When prompted for input)

## Folder Structure

```
handlers/       # Role-specific business logic
models/         # Data models and domain entities
persistence/    # JSON storage and data access layer
cli/            # Command-line interface components
backups/        # Generated system snapshots
```

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