"""AYON List Creator server addon."""

from typing import Type

from ayon_server.addons import BaseServerAddon
from nxtools import logging

from .settings import ListCreatorSettings
from .actions import CreateListsAction, CreateCustomListAction


class ListCreatorAddon(BaseServerAddon):
    """AYON List Creator addon for automated list creation."""

    settings_model: Type[ListCreatorSettings] = ListCreatorSettings
    actions = [CreateListsAction, CreateCustomListAction]

    async def get_default_settings(self):
        """Return default settings."""
        settings_model_cls = self.get_settings_model()
        return settings_model_cls(**{})

    def initialize(self):
        """Initialize the addon and register API endpoints."""
        from .api import router
        self.add_endpoint("/api", router, "List Creator API")
        logging.info("List Creator addon initialized with API endpoints")
