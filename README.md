# AYON List Creator

A standalone service for creating entity lists in AYON using the REST API.

## Overview

This service provides automated list creation functionality for AYON projects. It creates lists based on configured schedules and templates, directly using the AYON REST API without any external dependencies.

## Features

- **Automated List Creation**: Schedule list creation at specific times and days
- **Flexible Naming**: Use date/time templates for dynamic list names (e.g., `{yy}{mm}{dd}`)
- **Project-Based Configuration**: Different settings for each project
- **Direct AYON Integration**: Uses native AYON REST API endpoints

## Installation

```bash
pip install ayon-api
```

## Usage

### As a Service

Run the service to start automated list creation:

```bash
python -m services.processor.processor
```

The service will:
1. Load configuration from AYON settings
2. Schedule list creation based on configured times
3. Create lists automatically when triggered

### As a Library

You can also use the list creator programmatically:

```python
from services.processor.processor import AyonListCreator

# Create instance
creator = AyonListCreator()

# Start automated scheduling
creator.start()

# Or create lists manually
list_defs = [
    {
        "name_template": "{yy}{mm}{dd}",
        "entity_ids": ["entity_id_1", "entity_id_2"]
    }
]
creator._process_lists_creation({"my_project": list_defs})

# Stop when done
creator.stop()
```

## Configuration

Configure list creation in AYON project settings under the `create_daily_lists` key:

```json
{
  "enabled": true,
  "cycle_hour_start": "00:00:00",
  "cycle_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
  "lists": [
    {
      "name_template": "{yy}{mm}{dd}",
      "cycle_enabled": true,
      "entity_ids": []
    }
  ]
}
```

### Configuration Options

- **enabled**: Enable/disable list creation for this project
- **cycle_hour_start**: Time to run automated list creation (HH:MM:SS format)
- **cycle_days**: Days of the week to run (monday-sunday)
- **lists**: Array of list definitions
  - **name_template**: Template for list name using date/time placeholders
  - **cycle_enabled**: Enable/disable this specific list
  - **entity_ids**: Array of entity IDs to include in the list

### Name Template Placeholders

- `{d}`, `{dd}`: Day (1-31)
- `{ddd}`: Day name abbreviated (Mon, Tue, etc.)
- `{dddd}`: Day name full (Monday, Tuesday, etc.)
- `{m}`, `{mm}`: Month (1-12)
- `{mmm}`: Month name abbreviated (Jan, Feb, etc.)
- `{mmmm}`: Month name full (January, February, etc.)
- `{yy}`: Year (2-digit)
- `{yyyy}`: Year (4-digit)
- `{H}`, `{HH}`: Hour (0-23)
- `{M}`, `{MM}`: Minute (0-59)
- `{S}`, `{SS}`: Second (0-59)

## AYON REST API Endpoints

The service uses the following AYON REST API endpoints:

- `POST /api/projects/{project_name}/lists` - Create a new list
- `POST /api/projects/{project_name}/lists/{list_id}/items` - Add items to a list

## Migration from ftrack

This service was migrated from a ftrack-based implementation. See [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md) for details on the changes.

## File Structure

```
services/
└── processor/
    └── processor/
        ├── __init__.py              # Module exports
        ├── __main__.py              # Entry point
        └── default_handlers/
            └── action_create_lists.py  # Main list creation logic
```

## Requirements

- Python 3.7+
- ayon-api

## License

See [LICENSE](LICENSE) file for details.

## Contributing

This is a minimal, focused implementation for list creation. Contributions should maintain the simplicity and single-purpose nature of this service.
