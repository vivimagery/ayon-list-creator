"""AYON List Creator server addon."""

from typing import Type

from ayon_server.addons import BaseServerAddon

from .settings import ListCreatorSettings


class ListCreatorAddon(BaseServerAddon):
    """AYON List Creator addon for automated list creation."""

    settings_model: Type[ListCreatorSettings] = ListCreatorSettings

    async def get_default_settings(self):
        """Return default settings."""
        settings_model_cls = self.get_settings_model()
        return settings_model_cls(**{})
