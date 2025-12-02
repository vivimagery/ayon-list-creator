"""REST API endpoints for List Creator."""

import datetime
from typing import Any

from ayon_server.api.dependencies import (
    CurrentUser,
    ProjectName,
)
from ayon_server.exceptions import BadRequestException
from fastapi import APIRouter, Depends
from pydantic import BaseModel


class CreateListRequest(BaseModel):
    """Request model for creating a list."""

    name_template: str
    entity_type: str = "version"
    entity_ids: list[str] = []


class CreateListResponse(BaseModel):
    """Response model for list creation."""

    success: bool
    list_id: str | None = None
    list_name: str | None = None
    message: str | None = None


router = APIRouter(
    prefix="/list-creator",
    tags=["List Creator"],
)


@router.post(
    "/projects/{project_name}/create-list",
    response_model=CreateListResponse,
)
async def create_list_endpoint(
    project_name: ProjectName,
    request: CreateListRequest,
    user: CurrentUser = Depends(),
) -> CreateListResponse:
    """Create a new list in AYON.

    Args:
        project_name: Name of the project.
        request: List creation request.
        user: Current user.

    Returns:
        Response with list creation result.
    """
    try:
        # Import here to avoid circular imports
        import uuid
        import ayon_api

        # Fill the name template with current date/time
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

        list_name = request.name_template.format(**fill_data)
        list_id = str(uuid.uuid4().hex)[:24]

        # Create the list via AYON API
        payload = {
            "id": list_id,
            "entityListType": "generic",
            "entityType": request.entity_type,
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
        if request.entity_ids:
            for idx, entity_id in enumerate(request.entity_ids):
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

        return CreateListResponse(
            success=True,
            list_id=list_id,
            list_name=list_name,
            message=f"Successfully created list '{list_name}' with {len(request.entity_ids)} items.",
        )

    except Exception as e:
        return CreateListResponse(
            success=False,
            message=f"Failed to create list: {str(e)}",
        )


@router.get(
    "/projects/{project_name}/list-templates",
)
async def get_list_templates(
    project_name: ProjectName,
    user: CurrentUser = Depends(),
) -> dict[str, Any]:
    """Get list templates from project settings.

    Args:
        project_name: Name of the project.
        user: Current user.

    Returns:
        List templates configuration.
    """
    # This would retrieve the list templates from project settings
    # For now, return a placeholder
    return {
        "enabled": True,
        "lists": [],
    }
