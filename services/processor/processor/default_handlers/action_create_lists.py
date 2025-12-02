"""AYON List Creator - Processor for tracking new projects."""

import uuid
import threading
import datetime
import logging
from typing import List, Dict, Set

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
    """Processor for tracking new Project folders in AYON.

    Runs every 5 minutes and checks the ImmersRender project for new folders.
    """

    TARGET_PROJECT = "ImmersRender"
    RUN_INTERVAL_SECONDS = 300  # 5 minutes

    def __init__(self):
        """Initialize the list creator."""
        self._timer = None
        self.log = logging.getLogger(self.__class__.__name__)

        # Configure logging if not already configured
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

    def start(self):
        """Start the processor service."""
        self.log.info("Starting AYON List Creator service")
        self.log.info(f"Running every {self.RUN_INTERVAL_SECONDS} seconds")
        self._schedule_next_run()

    def stop(self):
        """Stop the processor service."""
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self.log.info("AYON List Creator service stopped")

    def _schedule_next_run(self):
        """Schedule the next run."""
        self._timer = threading.Timer(self.RUN_INTERVAL_SECONDS, self._run)
        self._timer.start()

    def _run(self):
        """Execute list update process."""
        try:
            self._process_projects()
        except Exception as e:
            self.log.error(f"Error during run: {e}", exc_info=True)

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
                # Check both 'name' and 'label' fields
                if (existing_list.get("name") == list_name or
                    existing_list.get("label") == list_name):
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

        payload = {
            "name": list_name,
            "entityType": "folder"
        }

        try:
            response = ayon_api.post(f"projects/{project_name}/lists", **payload)
            response.raise_for_status()
            list_data = response.data
            list_id = list_data.get("id")
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
        payload = {
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
