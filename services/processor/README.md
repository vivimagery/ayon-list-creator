# AYON List Creator - Processor Service

Daily processor service that automatically tracks Project folders in AYON and maintains monthly lists.

## What it does

- Runs daily at a scheduled time
- Checks the **ImmersRender** AYON project for folders with `folderType="Project"`
- Creates monthly lists with Russian names (e.g., "Наработка_Декабрь")
- Adds new Project folders to the current month's list
- Automatically creates a new list when the month changes

## Configuration

### Run Schedule

Configure when the processor runs daily using environment variables:

```bash
# Run at 9:00 AM (default)
LIST_CREATOR_RUN_HOUR=9
LIST_CREATOR_RUN_MINUTE=0

# Example: Run at 14:30 (2:30 PM)
LIST_CREATOR_RUN_HOUR=14
LIST_CREATOR_RUN_MINUTE=30
```

### Setup

1. Copy `example_env` to `.env`:
   ```bash
   cp example_env .env
   ```

2. Edit `.env` with your settings:
   ```bash
   AYON_SERVER_URL=http://your-ayon-server:5000
   AYON_API_KEY=your-api-key-here
   LIST_CREATOR_RUN_HOUR=9
   LIST_CREATOR_RUN_MINUTE=0
   ```

## Running

### Development (with Docker)

```bash
# PowerShell
.\manage.ps1 build
.\manage.ps1 dev

# Linux/Mac
make build
make dev
```

### Production (docker-compose)

```bash
docker-compose up -d
```

## Logs

The processor logs:
- When it starts
- Next scheduled run time
- Each project it processes
- New folders detected and added to lists
- Any errors encountered

Example output:
```
2024-12-02 09:00:00 - AyonListCreator - INFO - Starting AYON List Creator service
2024-12-02 09:00:00 - AyonListCreator - INFO - Daily run time: 09:00
2024-12-02 09:00:00 - AyonListCreator - INFO - Next run scheduled at 2024-12-03 09:00:00
2024-12-03 09:00:00 - AyonListCreator - INFO - Processing project: ImmersRender
2024-12-03 09:00:00 - AyonListCreator - INFO - Found 5 folders with folderType='Project'
2024-12-03 09:00:00 - AyonListCreator - INFO - New folder detected: Project_ABC
2024-12-03 09:00:00 - AyonListCreator - INFO - Added 1 new folders to list
```

## Target Project

To change which AYON project to track, edit `TARGET_PROJECT` in:
```
processor/default_handlers/action_create_lists.py
```

Currently set to: **ImmersRender**
