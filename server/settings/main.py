"""Settings models for AYON List Creator."""

from ayon_server.settings import BaseSettingsModel, SettingsField


def week_days():
    """Return week day enum options."""
    return [
        {"label": "Monday", "value": "monday"},
        {"label": "Tuesday", "value": "tuesday"},
        {"label": "Wednesday", "value": "wednesday"},
        {"label": "Thursday", "value": "thursday"},
        {"label": "Friday", "value": "friday"},
        {"label": "Saturday", "value": "saturday"},
        {"label": "Sunday", "value": "sunday"},
    ]


def default_week_days():
    """Return default week days (Monday-Friday)."""
    return ["monday", "tuesday", "wednesday", "thursday", "friday"]


class DailyListItemModel(BaseSettingsModel):
    """Configuration for a single list to be created."""

    _layout = "expanded"

    name_template: str = SettingsField(
        default="{yy}{mm}{dd}",
        title="Name template",
        description=(
            "Template for list name. Available placeholders: "
            "{yy}, {yyyy}, {mm}, {m}, {dd}, {d}, {HH}, {MM}, {SS}"
        ),
    )

    cycle_enabled: bool = SettingsField(
        default=False,
        title="Run automatically",
        description="Enable automatic creation of this list based on schedule",
    )

    entity_ids: list[str] = SettingsField(
        default_factory=list,
        title="Entity IDs",
        description=(
            "List of AYON entity IDs to include in the list. "
            "Leave empty to populate manually or via custom logic."
        ),
    )


class CreateDailyListsModel(BaseSettingsModel):
    """Configuration for automated list creation."""

    _isGroup = True

    enabled: bool = SettingsField(
        default=True,
        title="Enabled",
        description="Enable automated list creation for this project",
    )

    cycle_hour_start: str = SettingsField(
        default="00:00:00",
        title="Create daily lists at",
        description="Time when lists should be created automatically (HH:MM:SS)",
        widget="time",
        regex=r"(?:[01]\d|2[0123]):(?:[012345]\d):(?:[012345]\d)",
        section="Automated execution",
        scope=["studio"],
    )

    cycle_days: list[str] = SettingsField(
        default_factory=default_week_days,
        title="Days of week",
        description="Days when lists should be created automatically",
        enum_resolver=week_days,
        scope=["studio"],
    )

    lists: list[DailyListItemModel] = SettingsField(
        default_factory=list,
        title="Lists",
        description="List definitions to create",
    )


class ListCreatorSettings(BaseSettingsModel):
    """Main settings for AYON List Creator addon."""

    create_daily_lists: CreateDailyListsModel = SettingsField(
        default_factory=CreateDailyListsModel,
        title="Create Daily Lists",
        description="Configure automated list creation",
    )
