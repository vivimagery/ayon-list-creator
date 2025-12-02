# Settings Guide for AYON List Creator

## Overview

The AYON List Creator uses AYON's native settings system to configure automated list creation. Settings can be configured at both the **studio level** (global) and **project level** (per-project).

## Settings Structure

### Studio Settings (Global)

These settings apply across all projects:

- **Cycle Hour Start**: Time when lists should be created (HH:MM:SS format)
- **Cycle Days**: Days of the week when lists should be created

### Project Settings

Each project can have its own list creation configuration:

- **Enabled**: Enable/disable list creation for this project
- **Lists**: Array of list definitions to create

## Accessing Settings in AYON

### 1. Studio Settings

Go to AYON Server → **Studio Settings** → **List Creator** → **Create Daily Lists**

Configure global timing:
```
Automated execution:
  - Create daily lists at: 00:00:00
  - Days of week: [Monday, Tuesday, Wednesday, Thursday, Friday]
```

### 2. Project Settings

Go to AYON Server → **Project Settings** → Select Project → **List Creator** → **Create Daily Lists**

Configure project-specific lists:
```json
{
  "enabled": true,
  "lists": [
    {
      "name_template": "{yy}{mm}{dd}",
      "cycle_enabled": true,
      "entity_ids": []
    }
  ]
}
```

## Settings Model

### CreateDailyListsModel

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable automated list creation |
| `cycle_hour_start` | string | `"00:00:00"` | Time to create lists (HH:MM:SS) |
| `cycle_days` | array | `["monday"..."friday"]` | Days to run automation |
| `lists` | array | `[]` | List definitions |

### DailyListItemModel

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name_template` | string | `"{yy}{mm}{dd}"` | Template for list name |
| `cycle_enabled` | boolean | `false` | Enable auto-creation of this list |
| `entity_ids` | array | `[]` | AYON entity IDs to include |

## Name Template Placeholders

Use these placeholders in `name_template`:

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{d}` | Day (no padding) | 1, 15, 31 |
| `{dd}` | Day (padded) | 01, 15, 31 |
| `{ddd}` | Day name (short) | Mon, Tue, Wed |
| `{dddd}` | Day name (full) | Monday, Tuesday |
| `{m}` | Month (no padding) | 1, 6, 12 |
| `{mm}` | Month (padded) | 01, 06, 12 |
| `{mmm}` | Month name (short) | Jan, Feb, Mar |
| `{mmmm}` | Month name (full) | January, February |
| `{yy}` | Year (2-digit) | 24, 25 |
| `{yyyy}` | Year (4-digit) | 2024, 2025 |
| `{H}` | Hour (no padding) | 0, 5, 23 |
| `{HH}` | Hour (padded) | 00, 05, 23 |
| `{M}` | Minute (no padding) | 0, 5, 59 |
| `{MM}` | Minute (padded) | 00, 05, 59 |
| `{S}` | Second (no padding) | 0, 5, 59 |
| `{SS}` | Second (padded) | 00, 05, 59 |

## Configuration Examples

### Example 1: Daily Lists

Create a new list every day with the date as the name:

```json
{
  "enabled": true,
  "cycle_hour_start": "00:00:00",
  "cycle_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
  "lists": [
    {
      "name_template": "{yyyy}-{mm}-{dd}",
      "cycle_enabled": true,
      "entity_ids": []
    }
  ]
}
```

Result: Lists named "2024-12-02", "2024-12-03", etc.

### Example 2: Weekly Lists

Create a weekly list every Monday:

```json
{
  "enabled": true,
  "cycle_hour_start": "09:00:00",
  "cycle_days": ["monday"],
  "lists": [
    {
      "name_template": "Week_{yy}{mm}{dd}",
      "cycle_enabled": true,
      "entity_ids": []
    }
  ]
}
```

Result: Lists named "Week_241202", "Week_241209", etc.

### Example 3: Multiple Lists

Create multiple lists with different templates:

```json
{
  "enabled": true,
  "lists": [
    {
      "name_template": "Daily_{yy}{mm}{dd}",
      "cycle_enabled": true,
      "entity_ids": []
    },
    {
      "name_template": "Review_{dddd}",
      "cycle_enabled": true,
      "entity_ids": []
    }
  ]
}
```

Result: "Daily_241202" and "Review_Monday"

### Example 4: Manual Lists with Entity IDs

Create a list with specific entities:

```json
{
  "enabled": true,
  "lists": [
    {
      "name_template": "Shot_Review",
      "cycle_enabled": false,
      "entity_ids": [
        "ca097542ce3611f0a6bf0242ac120005",
        "ca097543ce3611f0a6bf0242ac120006"
      ]
    }
  ]
}
```

## How Settings Are Retrieved

The list creator retrieves settings in this order:

1. **Studio Settings** (for timing and days)
   ```python
   service_settings = get_service_addon_settings()
   action_settings = service_settings.get("create_daily_lists", {})
   ```

2. **Project Settings** (for list definitions)
   ```python
   project_settings = get_addon_settings(
       addon_name,
       addon_version,
       project_name
   )
   action_settings = project_settings.get("create_daily_lists", {})
   ```

## Programmatic Access

You can also access settings programmatically:

```python
from ayon_api import (
    get_addon_settings,
    get_service_addon_name,
    get_service_addon_version,
    get_service_addon_settings,
)

# Get studio settings
service_settings = get_service_addon_settings()
list_settings = service_settings.get("create_daily_lists", {})

# Get project settings
project_settings = get_addon_settings(
    get_service_addon_name(),
    get_service_addon_version(),
    "my_project"
)
list_settings = project_settings.get("create_daily_lists", {})
```

## Settings Validation

The AYON server validates all settings using the Pydantic models defined in `server/settings/main.py`:

- **Time format**: Must match `HH:MM:SS` (e.g., "09:30:00")
- **Days**: Must be from ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
- **Name template**: Any string with optional placeholders
- **Entity IDs**: Must be valid AYON entity IDs

## Defaults

If no settings are configured, these defaults apply:

```json
{
  "enabled": true,
  "cycle_hour_start": "00:00:00",
  "cycle_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
  "lists": []
}
```

## Troubleshooting

### Lists Not Being Created

1. Check that `enabled` is `true` at the project level
2. Verify `cycle_enabled` is `true` for each list
3. Check that the current day is in `cycle_days`
4. Verify the service is running
5. Check service logs for errors

### Invalid Settings

If settings are invalid:
- The AYON server will show validation errors in the UI
- Check that time format is correct (HH:MM:SS)
- Verify day names are lowercase and valid
- Ensure entity IDs are valid UUIDs

### Settings Not Taking Effect

- Settings are loaded when the service starts or on scheduled runs
- Restart the service to reload settings immediately
- Check the service logs for "Failed to get settings" warnings
