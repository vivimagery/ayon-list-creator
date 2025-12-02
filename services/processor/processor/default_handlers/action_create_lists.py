import json
import uuid
import threading
import datetime
from typing import Any, Union

import ayon_api
from ayon_api import (
    get_addon_settings,
    get_service_addon_name,
    get_service_addon_version,
    get_service_addon_settings,
)

WEEKDAY_MAPPING = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}


class AyonListCreator:
    """Handler for creating entity lists directly in AYON using REST API."""

    identifier = "create.daily.lists"
    settings_key = "create_daily_lists"
    automated_topic = "{}.automated".format(identifier)

    def __init__(self):
        self._cycle_timers_by_id = {}
        self._day_delta = datetime.timedelta(days=1)
        self.log = ayon_api.Logger.get_logger(self.__class__.__name__)

    def _calculate_next_cycle_delta(self, action_settings=None):
        """Calculate seconds until next scheduled list creation."""
        if action_settings is None:
            service_settings = get_service_addon_settings()
            action_settings = service_settings.get(self.settings_key, {})

        cycle_hour_start = action_settings.get("cycle_hour_start")
        if not cycle_hour_start:
            h = m = s = 0
        else:
            h, m, s = [int(v) for v in cycle_hour_start.split(":")]

        now = datetime.datetime.now()
        expected_next_trigger = datetime.datetime(
            now.year, now.month, now.day, h, m, s
        )
        if expected_next_trigger <= now:
            expected_next_trigger += self._day_delta
        return (expected_next_trigger - now).total_seconds()

    def start(self):
        """Start the automated list creation timer."""
        self._add_timer_callback()

    def stop(self):
        """Stop all timers."""
        for timer_id in list(self._cycle_timers_by_id.keys()):
            timer = self._cycle_timers_by_id.pop(timer_id, None)
            if timer is not None:
                timer.cancel()

    def _add_timer_callback(self):
        """Add a timer to trigger list creation at scheduled time."""
        seconds_delta = self._calculate_next_cycle_delta()

        timer_id = uuid.uuid4().hex
        cycle_timer = threading.Timer(
            seconds_delta, self._timer_callback, [timer_id]
        )
        self._cycle_timers_by_id[timer_id] = cycle_timer
        cycle_timer.start()

    def _timer_callback(self, timer_id):
        """Timer callback to trigger automated list creation."""
        timer = self._cycle_timers_by_id.pop(timer_id, None)
        if timer is None:
            return

        service_settings = get_service_addon_settings()
        action_settings = service_settings.get(self.settings_key, {})

        # Schedule next timer
        self._add_timer_callback()

        datetime_obj = datetime.datetime.now()
        weekday = WEEKDAY_MAPPING[datetime_obj.weekday()]

        if weekday not in action_settings.get("cycle_days", []):
            self.log.debug(
                f"Automated run on day {weekday} skipped by settings."
            )
            return

        # Trigger automated list creation
        self._automated_run()

    def _automated_run(self):
        """Run automated list creation for all enabled projects."""
        # Get all AYON projects
        ayon_projects = ayon_api.get_projects(fields=["name"])

        # Get action settings for each project
        action_settings_by_project = self._get_action_settings(
            [project["name"] for project in ayon_projects]
        )

        lists_by_project = {}
        for project_name, action_settings in action_settings_by_project.items():
            if not action_settings.get("enabled"):
                continue

            action_lists = [
                item
                for item in action_settings.get("lists", [])
                if item.get("cycle_enabled")
            ]
            if action_lists:
                lists_by_project[project_name] = action_lists

        if not lists_by_project:
            self.log.info(
                "No projects have enabled automated list creation"
            )
            return

        # Process list creation for each project
        self._process_lists_creation(lists_by_project)

    def _process_lists_creation(
        self, lists_by_project: dict[str, list[dict[str, Any]]]
    ):
        """Process list creation for multiple projects.

        Args:
            lists_by_project: Dictionary mapping project names to list definitions.
        """
        now = datetime.datetime.now()
        today_obj = datetime.datetime(
            now.year, now.month, now.day, 0, 0, 0
        )

        # Prepare fill data for list name templates
        fill_data = self._get_datetime_data(today_obj)

        for project_name, list_defs in lists_by_project.items():
            self._create_lists(project_name, list_defs, fill_data)

    def _get_datetime_data(self, datetime_obj: datetime.datetime) -> dict[str, Any]:
        """Get formatted date/time data for list name templates.

        Args:
            datetime_obj: Datetime object to format.

        Returns:
            Dictionary with formatted date/time strings.
        """
        return {
            "d": datetime_obj.strftime("%d"),
            "dd": datetime_obj.strftime("%d"),
            "ddd": datetime_obj.strftime("%a"),
            "dddd": datetime_obj.strftime("%A"),
            "m": str(datetime_obj.month),
            "mm": datetime_obj.strftime("%m"),
            "mmm": datetime_obj.strftime("%b"),
            "mmmm": datetime_obj.strftime("%B"),
            "yy": datetime_obj.strftime("%y"),
            "yyyy": datetime_obj.strftime("%Y"),
            "H": str(datetime_obj.hour),
            "HH": datetime_obj.strftime("%H"),
            "M": str(datetime_obj.minute),
            "MM": datetime_obj.strftime("%M"),
            "S": str(datetime_obj.second),
            "SS": datetime_obj.strftime("%S"),
        }

    def _create_project_list(
        self,
        project_name: str,
        list_name: str,
        entity_type: str = "version",
        entity_list_type: str = "generic",
    ) -> Union[dict[str, Any], None]:
        """Create a new list in AYON using REST API.

        Args:
            project_name: Name of the project.
            list_name: Name of the list to create.
            entity_type: Type of entities in the list (folder, product, version, etc.).
            entity_list_type: Type of the list (generic, etc.).

        Returns:
            Created list data or None if creation failed.
        """
        list_id = str(uuid.uuid4().hex)[:24]  # Generate shorter ID

        payload = {
            "id": list_id,
            "entityListType": entity_list_type,
            "entityType": entity_type,
            "label": list_name,
            "active": True,
            "items": []
        }

        try:
            response = ayon_api.post(
                f"projects/{project_name}/lists",
                **payload
            )
            response.raise_for_status()
            self.log.info(
                f"Created list '{list_name}' in project '{project_name}'"
            )
            return {"id": list_id, "label": list_name}
        except Exception as e:
            self.log.error(
                f"Failed to create list '{list_name}' "
                f"in project '{project_name}': {e}"
            )
            return None

    def _add_items_to_list(
        self,
        project_name: str,
        list_id: str,
        entity_ids: list[str]
    ) -> bool:
        """Add items to an existing list in AYON using REST API.

        Args:
            project_name: Name of the project.
            list_id: ID of the list.
            entity_ids: List of entity IDs to add to the list.

        Returns:
            True if successful, False otherwise.
        """
        if not entity_ids:
            return True

        try:
            # Add each entity as a list item
            for idx, entity_id in enumerate(entity_ids):
                item_payload = {
                    "id": str(uuid.uuid4().hex)[:24],
                    "entityId": entity_id,
                    "position": idx,
                }

                response = ayon_api.post(
                    f"projects/{project_name}/lists/{list_id}/items",
                    **item_payload
                )
                response.raise_for_status()

            self.log.info(
                f"Added {len(entity_ids)} items to list '{list_id}' "
                f"in project '{project_name}'"
            )
            return True
        except Exception as e:
            self.log.error(
                f"Failed to add items to list '{list_id}' "
                f"in project '{project_name}': {e}"
            )
            return False

    def _create_lists(
        self,
        project_name: str,
        list_defs: list[dict[str, Any]],
        fill_data: dict[str, Any],
    ):
        """Create lists in AYON for a project.

        Args:
            project_name: Name of the project.
            list_defs: List definitions from settings.
            fill_data: Date/time data for list name templates.
        """
        for list_def in list_defs:
            name_template = list_def.get("name_template", "{yy}{mm}{dd}")
            list_name = self._fill_list_name_template(name_template, fill_data)
            if list_name is None:
                continue

            # Get entity IDs from list definition (if provided)
            # This is a simplified version - in reality, you would query
            # AYON for entities matching the list criteria
            entity_ids = list_def.get("entity_ids", [])

            # Create the list
            created_list = self._create_project_list(
                project_name=project_name,
                list_name=list_name,
                entity_type="version",  # Default to version entities
            )

            if created_list and entity_ids:
                # Add items to the list
                self._add_items_to_list(
                    project_name=project_name,
                    list_id=created_list["id"],
                    entity_ids=entity_ids
                )

    def _get_action_settings(
        self, project_names: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Get action settings for multiple projects.

        Args:
            project_names: List of project names.

        Returns:
            Dictionary mapping project names to their action settings.
        """
        settings_by_project = {}
        for project_name in project_names:
            try:
                project_settings = get_addon_settings(
                    get_service_addon_name(),
                    get_service_addon_version(),
                    project_name,
                )
                action_settings = project_settings.get(self.settings_key, {})
                settings_by_project[project_name] = action_settings
            except Exception as e:
                self.log.warning(
                    f"Failed to get settings for project '{project_name}': {e}"
                )
                settings_by_project[project_name] = {}
        return settings_by_project

    def _fill_list_name_template(
        self, template: str, data: dict[str, Any]
    ) -> Union[str, None]:
        """Fill list name template with date/time data.

        Args:
            template: Template string with placeholders (e.g., "{yy}{mm}{dd}").
            data: Dictionary with date/time values.

        Returns:
            Filled template string or None if formatting failed.
        """
        try:
            return template.format(**data)
        except Exception:
            self.log.warning(
                f"Failed to fill list template '{template}' with data {data}",
                exc_info=True
            )
            return None
