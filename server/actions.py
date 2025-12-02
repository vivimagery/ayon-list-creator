"""AYON Actions for List Creator."""

from typing import Any

from ayon_server.actions import (
    ActionExecutor,
    ExecuteResponseModel,
    LauncherAction,
)


class CreateListsAction(LauncherAction):
    """Action to manually create lists in AYON."""

    identifier = "create_lists_manual"
    label = "Create Lists"
    category = "Lists"
    icon = "playlist_add"

    def get_form(
        self,
        project_name: str,
        variant: str = "production",
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """Return form definition for list creation.

        Args:
            project_name: Name of the project.
            variant: Settings variant.
            **kwargs: Additional arguments.

        Returns:
            Form definition or None.
        """
        # Get project settings
        addon = self.get_addon()
        settings = addon.get_project_settings(project_name, variant)
        list_config = settings.get("create_daily_lists", {})

        if not list_config.get("enabled"):
            return {
                "type": "label",
                "value": "List creation is disabled for this project. "
                        "Enable it in Project Settings.",
            }

        lists = list_config.get("lists", [])
        if not lists:
            return {
                "type": "label",
                "value": "No lists configured. Add list definitions in Project Settings.",
            }

        # Build form with checkboxes for each list
        fields = [
            {
                "type": "label",
                "value": "## Select lists to create:",
            }
        ]

        for idx, list_def in enumerate(lists):
            name_template = list_def.get("name_template", "Unnamed")
            fields.append({
                "type": "separator",
            })
            fields.append({
                "type": "label",
                "value": f"**{name_template}**",
            })
            fields.append({
                "type": "boolean",
                "name": f"list_{idx}",
                "label": "Create this list",
                "value": False,
            })

        return {"fields": fields}

    async def execute(
        self,
        executor: ActionExecutor,
    ) -> ExecuteResponseModel:
        """Execute the list creation action.

        Args:
            executor: Action executor with form values.

        Returns:
            Execution response.
        """
        import ayon_api
        import datetime
        import uuid

        project_name = executor.context.project_name
        form_data = executor.data or {}

        # Get settings
        addon = self.get_addon()
        settings = addon.get_project_settings(
            project_name,
            executor.context.variant
        )
        list_config = settings.get("create_daily_lists", {})
        lists = list_config.get("lists", [])

        # Find selected lists
        selected_lists = []
        for idx, list_def in enumerate(lists):
            if form_data.get(f"list_{idx}"):
                selected_lists.append(list_def)

        if not selected_lists:
            return ExecuteResponseModel(
                success=False,
                message="No lists selected. Please select at least one list to create.",
            )

        # Fill date/time template data
        now = datetime.datetime.now()
        fill_data = {
            "d": now.strftime("%d"),
            "dd": now.strftime("%d"),
            "ddd": now.strftime("%a"),
            "dddd": now.strftime("%A"),
            "m": str(now.month),
            "mm": now.strftime("%m"),
            "mmm": now.strftime("%b"),
            "mmmm": now.strftime("%B"),
            "yy": now.strftime("%y"),
            "yyyy": now.strftime("%Y"),
            "H": str(now.hour),
            "HH": now.strftime("%H"),
            "M": str(now.minute),
            "MM": now.strftime("%M"),
            "S": str(now.second),
            "SS": now.strftime("%S"),
        }

        # Create each selected list
        created_lists = []
        errors = []

        for list_def in selected_lists:
            try:
                name_template = list_def.get("name_template", "{yy}{mm}{dd}")
                list_name = name_template.format(**fill_data)
                entity_ids = list_def.get("entity_ids", [])

                list_id = str(uuid.uuid4().hex)[:24]

                # Create the list
                payload = {
                    "id": list_id,
                    "entityListType": "generic",
                    "entityType": "version",
                    "label": list_name,
                    "active": True,
                    "items": [],
                }

                response = ayon_api.post(
                    f"projects/{project_name}/lists",
                    **payload
                )
                response.raise_for_status()

                # Add items if provided
                if entity_ids:
                    for idx, entity_id in enumerate(entity_ids):
                        item_payload = {
                            "id": str(uuid.uuid4().hex)[:24],
                            "entityId": entity_id,
                            "position": idx,
                        }

                        item_response = ayon_api.post(
                            f"projects/{project_name}/lists/{list_id}/items",
                            **item_payload
                        )
                        item_response.raise_for_status()

                created_lists.append(f"{list_name} ({len(entity_ids)} items)")

            except Exception as e:
                errors.append(f"{name_template}: {str(e)}")

        # Build result message
        message_parts = []
        if created_lists:
            message_parts.append(f"✓ Successfully created {len(created_lists)} list(s):")
            message_parts.extend([f"  - {name}" for name in created_lists])

        if errors:
            message_parts.append(f"\n✗ Failed to create {len(errors)} list(s):")
            message_parts.extend([f"  - {error}" for error in errors])

        return ExecuteResponseModel(
            success=len(errors) == 0,
            message="\n".join(message_parts),
        )


class CreateCustomListAction(LauncherAction):
    """Action to create a custom list with manual name."""

    identifier = "create_custom_list"
    label = "Create Custom List"
    category = "Lists"
    icon = "add_circle"

    def get_form(
        self,
        project_name: str,
        variant: str = "production",
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """Return form definition for custom list creation.

        Args:
            project_name: Name of the project.
            variant: Settings variant.
            **kwargs: Additional arguments.

        Returns:
            Form definition or None.
        """
        return {
            "fields": [
                {
                    "type": "label",
                    "value": "## Create a custom list",
                },
                {
                    "type": "text",
                    "name": "list_name",
                    "label": "List Name",
                    "placeholder": "Enter list name",
                    "required": True,
                },
                {
                    "type": "enum",
                    "name": "entity_type",
                    "label": "Entity Type",
                    "options": [
                        {"value": "folder", "label": "Folder"},
                        {"value": "product", "label": "Product"},
                        {"value": "version", "label": "Version"},
                        {"value": "representation", "label": "Representation"},
                        {"value": "task", "label": "Task"},
                        {"value": "workfile", "label": "Workfile"},
                    ],
                    "value": "version",
                },
                {
                    "type": "text",
                    "name": "entity_ids",
                    "label": "Entity IDs (comma-separated)",
                    "placeholder": "Leave empty or enter entity IDs",
                },
            ]
        }

    async def execute(
        self,
        executor: ActionExecutor,
    ) -> ExecuteResponseModel:
        """Execute the custom list creation action.

        Args:
            executor: Action executor with form values.

        Returns:
            Execution response.
        """
        import ayon_api
        import uuid

        project_name = executor.context.project_name
        form_data = executor.data or {}

        list_name = form_data.get("list_name", "").strip()
        entity_type = form_data.get("entity_type", "version")
        entity_ids_str = form_data.get("entity_ids", "").strip()

        if not list_name:
            return ExecuteResponseModel(
                success=False,
                message="List name is required.",
            )

        # Parse entity IDs
        entity_ids = []
        if entity_ids_str:
            entity_ids = [
                eid.strip()
                for eid in entity_ids_str.split(",")
                if eid.strip()
            ]

        try:
            list_id = str(uuid.uuid4().hex)[:24]

            # Create the list
            payload = {
                "id": list_id,
                "entityListType": "generic",
                "entityType": entity_type,
                "label": list_name,
                "active": True,
                "items": [],
            }

            response = ayon_api.post(
                f"projects/{project_name}/lists",
                **payload
            )
            response.raise_for_status()

            # Add items if provided
            if entity_ids:
                for idx, entity_id in enumerate(entity_ids):
                    item_payload = {
                        "id": str(uuid.uuid4().hex)[:24],
                        "entityId": entity_id,
                        "position": idx,
                    }

                    item_response = ayon_api.post(
                        f"projects/{project_name}/lists/{list_id}/items",
                        **item_payload
                    )
                    item_response.raise_for_status()

            return ExecuteResponseModel(
                success=True,
                message=(
                    f"✓ Successfully created list '{list_name}'\n"
                    f"  Entity type: {entity_type}\n"
                    f"  Items: {len(entity_ids)}"
                ),
            )

        except Exception as e:
            return ExecuteResponseModel(
                success=False,
                message=f"✗ Failed to create list: {str(e)}",
            )
