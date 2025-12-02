# Actions Guide for AYON List Creator

## Overview

AYON List Creator provides **actions** (buttons) in the AYON web UI that allow you to manually create lists, similar to how ftrack actions worked.

## Available Actions

### 1. Create Lists

**Action Name:** "Create Lists"
**Category:** Lists
**Icon:** 📋 (playlist_add)

This action allows you to create lists from your configured templates.

#### How to Use

1. **Open AYON Web UI** and navigate to a project
2. **Click the Actions button** (usually in the top right or context menu)
3. **Find "Create Lists"** under the "Lists" category
4. **Select which lists to create** - You'll see checkboxes for each list template configured in your settings
5. **Click Execute** - The action will create the selected lists immediately

#### What Happens

- The action reads list definitions from your project settings
- Shows a form with checkboxes for each configured list
- When you click Execute:
  - Fills the name template with current date/time
  - Creates the list in AYON using the REST API
  - Adds any configured entity IDs to the list
  - Shows a success/error message

#### Example

If you have these list templates configured:
```json
{
  "lists": [
    {
      "name_template": "{yyyy}-{mm}-{dd}",
      "cycle_enabled": true,
      "entity_ids": []
    },
    {
      "name_template": "Review_{dddd}",
      "cycle_enabled": false,
      "entity_ids": ["abc123", "def456"]
    }
  ]
}
```

The action will show:
```
Select lists to create:
---
**{yyyy}-{mm}-{dd}**
☐ Create this list
---
**Review_{dddd}**
☐ Create this list
```

When executed on December 2, 2024, it creates:
- List named "2024-12-02"
- List named "Review_Monday" with 2 items

---

### 2. Create Custom List

**Action Name:** "Create Custom List"
**Category:** Lists
**Icon:** ➕ (add_circle)

This action allows you to create a one-off custom list with a manual name.

#### How to Use

1. **Open AYON Web UI** and navigate to a project
2. **Click the Actions button**
3. **Find "Create Custom List"** under the "Lists" category
4. **Fill in the form:**
   - **List Name:** Enter the name for your list (e.g., "Shot Review")
   - **Entity Type:** Select the type of entities (Folder, Product, Version, etc.)
   - **Entity IDs:** Optionally enter comma-separated entity IDs
5. **Click Execute**

#### Form Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| List Name | Text | Yes | Name for the list |
| Entity Type | Dropdown | No | Type of entities (default: version) |
| Entity IDs | Text | No | Comma-separated entity IDs to add |

#### Example

Create a custom list for shot review:
```
List Name: "Shot 010 Review"
Entity Type: version
Entity IDs: ca097542ce3611f0a6bf0242ac120005, ca097543ce3611f0a6bf0242ac120006
```

Result:
- List named "Shot 010 Review"
- Entity type: version
- Contains 2 version entities

---

## Where Actions Appear

### In AYON Web UI

Actions can be accessed from:

1. **Global Actions Menu:**
   - Top right corner of the AYON interface
   - "Actions" button or three-dot menu

2. **Project Context:**
   - When viewing a specific project
   - Right-click context menus
   - Project toolbar

3. **Entity Context:**
   - When selecting folders, tasks, or versions
   - Right-click context menus

## How Actions Work

### Behind the Scenes

1. **Action Definition** (`server/actions.py`)
   - Defines the action UI (form fields, labels)
   - Handles form submission
   - Calls AYON REST API to create lists

2. **Settings Integration**
   - "Create Lists" action reads from project settings
   - Uses configured list templates
   - Applies name template placeholders

3. **API Calls**
   - Actions call `POST /api/projects/{project_name}/lists`
   - Creates list entities directly in AYON
   - Adds list items if entity IDs are provided

### Action Flow

```
User clicks action
     ↓
AYON shows form (defined in get_form())
     ↓
User fills form and clicks Execute
     ↓
Action's execute() method runs
     ↓
Reads settings / form data
     ↓
Creates list via AYON REST API
     ↓
Shows success/error message to user
```

## Comparison with ftrack Actions

| Feature | ftrack Actions | AYON Actions |
|---------|----------------|--------------|
| **Location** | ftrack web UI | AYON web UI |
| **Trigger** | Right-click menu | Actions menu |
| **Form UI** | ftrack dialog | AYON form dialog |
| **Execution** | ftrack action server | AYON server addon |
| **API** | ftrack API | AYON REST API |
| **Settings** | ftrack settings | AYON project settings |

## Permissions

Actions respect AYON's permission system:

- Users need appropriate permissions to create lists
- Actions may be restricted by role/user
- Check with your AYON administrator for permissions

## Troubleshooting

### Action Doesn't Appear

1. **Check addon is installed** - List Creator addon must be active
2. **Check project context** - Some actions only appear in project views
3. **Check permissions** - You may not have permission to run the action

### Action Fails to Create List

1. **Check error message** - The action shows detailed error messages
2. **Verify settings** - Ensure list templates are configured correctly
3. **Check entity IDs** - Entity IDs must be valid AYON entity UUIDs
4. **Check permissions** - You need permission to create lists in the project

### No Lists Shown in "Create Lists" Action

1. **Check settings** - Go to Project Settings → List Creator
2. **Add list definitions** - At least one list must be configured
3. **Enable list creation** - Ensure `enabled: true` in settings

## Advanced Usage

### Custom Actions

You can create custom actions by:

1. Adding new action classes to `server/actions.py`
2. Registering them in `server/__init__.py`
3. Defining custom forms and execution logic

Example:
```python
class MyCustomAction(LauncherAction):
    identifier = "my_custom_action"
    label = "My Custom Action"
    category = "Custom"

    def get_form(self, project_name, variant, **kwargs):
        # Define form fields
        pass

    async def execute(self, executor):
        # Execute action logic
        pass
```

### Programmatic Execution

While actions are designed for UI use, you can also trigger them programmatically:

```python
from ayon_api import execute_action

result = execute_action(
    action_identifier="create_custom_list",
    project_name="my_project",
    data={
        "list_name": "My List",
        "entity_type": "version",
        "entity_ids": ["id1", "id2"]
    }
)
```

## Further Reading

- [AYON Actions Documentation](https://ayon.ynput.io/docs/dev_addon_actions)
- [SETTINGS_GUIDE.md](SETTINGS_GUIDE.md) - Configure list templates
- [README.md](README.md) - General usage guide
