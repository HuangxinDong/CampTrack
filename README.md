> [!IMPORTANT]
> Because the project architecture was altered without discussion during development, the project has drifted from its intended direction. This repository will be where I explore my own approach. Just for fun.

# Scout Camp Management System

A CLI-based management system for Scout Camps. Originally developed for COMP0066 Course Project.

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
*   **Persistence**: SQLite-backed storage (persistence/data/camptrack.db) with automated JSON backup capabilities and seed-from-JSON utility.
*   **Authentication**: Role-based login with password confirmation and uniqueness checks.
*   **Weather Integration**: Real-time forecasting via Open-Meteo API for safe activity planning.



## Controls

*   `b`: Back / Cancel
*   `q`: Quit
*   `s`: Search (When prompted for input)

## Folder Structure

```
handlers/       # Presentation Layer: CLI interaction and menu logic
services/       # Business Logic Layer: Core rules, validation, and calculations
models/         # Domain Layer: Data entities
persistence/    # Data Access Layer: SQLite-backed DAO + schema/seed scripts
cli/            # UI Components: Display helpers and input utilities
persistence/data/          # SQLite db (camptrack.db), JSON seeds, backups/
```

## Architecture

The system follows a **Service-Repository Pattern** (Layered Architecture) backed by SQLite to ensure separation of concerns and testability:

1.  **Presentation Layer (`handlers/`)**: Handles user input and displays output. It delegates all business logic to Services.
2.  **Business Logic Layer (`services/`)**: Contains the core business rules (e.g., schedule conflict detection, validation, activity limits).
    *   `UserService`: User management and authentication rules.
    *   `CampService`: Camp creation, logistics, and resource management.
    *   `ActivityService`: Activity scheduling and library management.
    *   `ReportService`: Daily reporting, statistics, and NLP summary extraction.
3.  **Data Access Layer (`persistence/`)**: Manages data storage and retrieval (SQLite via `persistence/dao` using `persistence/db_context.py`).

## Setup

Requires Python 3.8+.

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  (Optional) Seed SQLite DB from existing JSON (creates persistence/data/camptrack.db):
    ```bash
    python -m persistence.seed_from_json
    ```

3.  Launch application:
    ```bash
    python main.py
    ```

4.  Run tests (fast regression):
    ```bash
    pytest -q
    ```