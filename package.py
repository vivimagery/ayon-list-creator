"""Package metadata for AYON List Creator addon."""

name = "list_creator"
version = "1.0.0"
title = "List Creator"

services = {
    "processor": {"image": f"ynput/ayon-list-creator:{version}"},
}

plugin_for = ["ayon_server"]

ayon_required_addons = {
    "core": ">=0.4.0",
}
