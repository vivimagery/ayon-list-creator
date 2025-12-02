# List Creation Migration: ftrack to AYON

## Overview
This document summarizes the migration of list creation logic from ftrack to AYON REST API.

## What Was Changed

### File Modified
- `services/processor/processor/default_handlers/action_create_lists.py`

### Key Changes

#### 1. **Removed ftrack Dependencies**
- Removed `ftrack_api` imports and session handling
- Removed `ftrack_common` imports (ServerAction, etc.)
- Removed all ftrack entity queries and operations

#### 2. **Removed Complex Filtering Logic**
All ftrack-specific filtering has been removed:
- Asset version queries from ftrack hierarchy
- Status filtering based on ftrack statuses
- Custom attribute filtering (hierarchical and non-hierarchical)
- Entity hierarchy traversal

#### 3. **Implemented AYON REST API Integration**
New methods using AYON REST API:

##### `_create_project_list()`
Creates lists directly in AYON using:
```python
POST /api/projects/{project_name}/lists
```

Payload structure:
```json
{
  "id": "string",
  "entityListType": "generic",
  "entityType": "version",
  "label": "List Name",
  "active": true,
  "items": []
}
```

##### `_add_items_to_list()`
Adds items to lists using:
```python
POST /api/projects/{project_name}/lists/{list_id}/items
```

Payload structure:
```json
{
  "id": "string",
  "entityId": "entity_id",
  "position": 0
}
```

#### 4. **Simplified Class Structure**
- Changed from `CreateDailyListServerAction` (ftrack action) to `AyonListCreator`
- Removed UI interface methods (`discover`, `interface`, `launch`)
- Kept timer-based automation functionality
- Simplified settings retrieval

#### 5. **Preserved Functionality**
- Timer-based scheduled list creation
- Weekday filtering (only run on specified days)
- List name templating with date/time variables
- Settings-based configuration per project

## New Class: `AyonListCreator`

### Key Methods

| Method | Purpose |
|--------|---------|
| `start()` | Start the automated list creation timer |
| `stop()` | Stop all timers |
| `_create_project_list()` | Create a new list in AYON via REST API |
| `_add_items_to_list()` | Add items to an existing list via REST API |
| `_create_lists()` | Main list creation logic for a project |
| `_get_datetime_data()` | Format datetime for list name templates |
| `_fill_list_name_template()` | Fill list name templates with date/time data |

### Usage Example

```python
# Initialize the creator
creator = AyonListCreator()

# Start automated list creation
creator.start()

# Or manually create lists for specific projects
list_defs = [
    {
        "name_template": "{yy}{mm}{dd}",
        "entity_ids": ["entity_id_1", "entity_id_2"]
    }
]
creator._process_lists_creation({"my_project": list_defs})

# Stop timers when done
creator.stop()
```

## What Was Removed

### ftrack-Specific Logic
1. **ftrack Session Management** - All `session.query()` and `session.create()` calls
2. **Entity Queries** - Querying TypedContext, Assets, AssetVersions from ftrack
3. **Custom Attribute Queries** - Both hierarchical and non-hierarchical attribute filtering
4. **Status Filtering** - ftrack status-based filtering of asset versions
5. **List Category Management** - ftrack ListCategory handling
6. **UI Action Methods** - `discover()`, `interface()`, `launch()` for ftrack actions
7. **ftrack Event Hub** - Event subscription and handling

### Removed Methods
- `_query_all_project_entity_ids()` - Queried ftrack entity hierarchy
- `_query_asset_versions()` - Queried asset versions from ftrack
- `_query_attr_values()` - Queried custom attribute values
- `_filter_asset_versions_for_list_def()` - Filtered versions by criteria
- `_filter_avs_by_list_filter()` - Applied filters to asset versions

## Settings Structure

The settings structure remains compatible:

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

## AYON REST API Endpoints Used

1. **Create List**: `POST /api/projects/{project_name}/lists`
2. **Add List Item**: `POST /api/projects/{project_name}/lists/{list_id}/items`

## Benefits of Migration

1. **No ftrack Dependency** - Direct AYON integration
2. **Simplified Logic** - Removed complex ftrack filtering
3. **REST API Based** - Standard HTTP API calls
4. **More Maintainable** - Cleaner, simpler codebase
5. **Better Separation** - Lists managed entirely in AYON

## Notes

- The current implementation is simplified and expects `entity_ids` to be provided in list definitions
- In a production environment, you may want to add logic to query AYON entities based on criteria
- Error handling includes logging and graceful failure
- List IDs are generated using UUID (shortened to 24 characters)

## Next Steps

To use this in production:

1. Ensure AYON REST API is accessible
2. Configure settings with appropriate list definitions
3. Provide entity IDs in list definitions or add querying logic
4. Test with a small project before rolling out
5. Monitor logs for any errors during list creation
