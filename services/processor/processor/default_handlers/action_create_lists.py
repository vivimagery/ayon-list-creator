"""AYON List Creator - Daily processor for tracking new projects."""

import uuid
import threading
import datetime
from typing import List, Dict, Set
import time

import ayon_api


# Russian month names for list naming
RUSSIAN_MONTHS = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь",
}


class AyonListCreator:
    """Daily processor for tracking new Project folders in AYON.

    This service:
    - Runs daily at a scheduled time
    - Checks the ImmersRender project for folders with folderType="Project"
    - Creates a monthly list (e.g., "Наработка_Май")
    - Adds new Project folders to the current month's list
    """

    # AYON project to track
    TARGET_PROJECT = "ImmersRender"

    def __init__(self, run_hour: int = 9, run_minute: int = 0):
        """Initialize the list creator.

        Args:
            run_hour: Hour of day to run (0-23), default 9 AM
            run_minute: Minute of hour to run (0-59), default 0
        """
        self.run_hour = run_hour
        self.run_minute = run_minute
        self._timer = None
        self._day_delta = datetime.timedelta(days=1)
        self.log = ayon_api.Logger.get_logger(self.__class__.__name__)

    def _calculate_next_run_time(self) -> float:
        """Calculate seconds until next scheduled run.

        Returns:
            Seconds until next run time.
        """
        now = datetime.datetime.now()
        next_run = datetime.datetime(
            now.year, now.month, now.day,
            self.run_hour, self.run_minute, 0
        )

        # If today's run time has passed, schedule for tomorrow
        if next_run <= now:
            next_run += self._day_delta

        delta_seconds = (next_run - now).total_seconds()
        self.log.info(
            f"Next run scheduled at {next_run.strftime('%Y-%m-%d %H:%M:%S')} "
            f"({delta_seconds / 3600:.1f} hours from now)"
        )
        return delta_seconds

    def start(self):
        """Start the daily processor service."""
        self.log.info("Starting AYON List Creator service")
        self.log.info(f"Daily run time: {self.run_hour:02d}:{self.run_minute:02d}")
        self._schedule_next_run()

    def stop(self):
        """Stop the processor service."""
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self.log.info("AYON List Creator service stopped")

    def _schedule_next_run(self):
        """Schedule the next daily run."""
        seconds_until_run = self._calculate_next_run_time()
        self._timer = threading.Timer(seconds_until_run, self._daily_run)
        self._timer.start()

    def _daily_run(self):
        """Execute daily list update process."""
        self.log.info("=" * 60)
        self.log.info("Starting daily list update")

        try:
            self._process_projects()
        except Exception as e:
            self.log.error(f"Error during daily run: {e}", exc_info=True)

        self.log.info("Daily list update completed")
        self.log.info("=" * 60)

        # Schedule next run
        self._schedule_next_run()

    def _get_current_month_list_name(self) -> str:
        """Get the list name for current month.

        Returns:
            List name like "Наработка_Май"
        """
        now = datetime.datetime.now()
        month_name = RUSSIAN_MONTHS[now.month]
        return f"Наработка_{month_name}"

    def _get_or_create_monthly_list(self, project_name: str) -> Dict:
        """Get or create the monthly list for a project.

        Args:
            project_name: Name of the AYON project

        Returns:
            Dictionary with list details (id, label)
        """
        list_name = self._get_current_month_list_name()

        # Check if list already exists
        try:
            response = ayon_api.get(f"projects/{project_name}/lists")
            response.raise_for_status()
            existing_lists = response.data.get("lists", [])

            for existing_list in existing_lists:
                if existing_list.get("label") == list_name:
                    self.log.debug(
                        f"Found existing list '{list_name}' in project '{project_name}'"
                    )
                    return existing_list
        except Exception as e:
            self.log.warning(
                f"Error checking existing lists in '{project_name}': {e}"
            )

        # Create new list
        self.log.info(f"Creating new list '{list_name}' in project '{project_name}'")
        list_id = str(uuid.uuid4().hex)[:24]

        payload = {
            "id": list_id,
            "entityListType": "generic",
            "entityType": "folder",
            "label": list_name,
            "active": True,
            "items": []
        }

        try:
            response = ayon_api.post(f"projects/{project_name}/lists", **payload)
            response.raise_for_status()
            self.log.info(f"Created list '{list_name}' with ID: {list_id}")
            return {"id": list_id, "label": list_name}
        except Exception as e:
            self.log.error(f"Failed to create list '{list_name}': {e}")
            raise

    def _get_list_folder_ids(self, project_name: str, list_id: str) -> Set[str]:
        """Get all folder IDs currently in the list.

        Args:
            project_name: Name of the AYON project
            list_id: ID of the list

        Returns:
            Set of folder IDs in the list
        """
        try:
            response = ayon_api.get(f"projects/{project_name}/lists/{list_id}/items")
            response.raise_for_status()
            items = response.data.get("items", [])
            return {item.get("entityId") for item in items if item.get("entityId")}
        except Exception as e:
            self.log.warning(
                f"Error getting list items for list '{list_id}': {e}"
            )
            return set()

    def _find_project_folders(self, project_name: str) -> List[Dict]:
        """Find all folders with folderType="Project" in a project.

        Args:
            project_name: Name of the AYON project

        Returns:
            List of folder dictionaries with 'id' and 'name'
        """
        try:
            # Query folders with folderType="Project"
            response = ayon_api.get(
                f"projects/{project_name}/folders",
                folderType="Project"
            )
            response.raise_for_status()
            folders = response.data.get("folders", [])

            project_folders = []
            for folder in folders:
                folder_id = folder.get("id")
                folder_name = folder.get("name")
                folder_type = folder.get("folderType")

                if folder_type == "Project" and folder_id and folder_name:
                    project_folders.append({
                        "id": folder_id,
                        "name": folder_name
                    })

            return project_folders
        except Exception as e:
            self.log.error(
                f"Error querying folders in project '{project_name}': {e}"
            )
            return []

    def _add_folder_to_list(
        self, project_name: str, list_id: str, folder_id: str, folder_name: str
    ):
        """Add a folder to a list.

        Args:
            project_name: Name of the AYON project
            list_id: ID of the list
            folder_id: ID of the folder to add
            folder_name: Name of the folder (for logging)
        """
        item_id = str(uuid.uuid4().hex)[:24]
        payload = {
            "id": item_id,
            "entityId": folder_id
        }

        try:
            response = ayon_api.post(
                f"projects/{project_name}/lists/{list_id}/items",
                **payload
            )
            response.raise_for_status()
            self.log.info(
                f"Added folder '{folder_name}' (ID: {folder_id}) to list"
            )
        except Exception as e:
            self.log.error(
                f"Failed to add folder '{folder_name}' to list: {e}"
            )

    def _process_projects(self):
        """Process the ImmersRender project and update monthly lists."""
        project_name = self.TARGET_PROJECT

        self.log.info(f"Processing project: {project_name}")

        try:
            # Verify project exists
            response = ayon_api.get(f"projects/{project_name}")
            response.raise_for_status()
        except Exception as e:
            self.log.error(
                f"Failed to access project '{project_name}': {e}. "
                "Make sure the project exists in AYON."
            )
            return

        try:
            # Get or create monthly list for this project
            monthly_list = self._get_or_create_monthly_list(project_name)
            list_id = monthly_list["id"]

            # Get folders already in the list
            existing_folder_ids = self._get_list_folder_ids(project_name, list_id)
            self.log.debug(
                f"List currently has {len(existing_folder_ids)} folders"
            )

            # Find all Project folders in this project
            project_folders = self._find_project_folders(project_name)
            self.log.info(
                f"Found {len(project_folders)} folders with folderType='Project'"
            )

            # Add new folders to the list
            new_folders_added = 0
            for folder in project_folders:
                folder_id = folder["id"]
                folder_name = folder["name"]

                if folder_id not in existing_folder_ids:
                    self.log.info(f"New folder detected: {folder_name}")
                    self._add_folder_to_list(
                        project_name, list_id, folder_id, folder_name
                    )
                    new_folders_added += 1

            if new_folders_added > 0:
                self.log.info(
                    f"Added {new_folders_added} new folders to list"
                )
            else:
                self.log.info("No new folders to add")

        except Exception as e:
            self.log.error(
                f"Error processing project '{project_name}': {e}",
                exc_info=True
            )
