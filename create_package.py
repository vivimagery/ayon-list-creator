#!/usr/bin/env python
"""Create AYON addon package for List Creator.

This script creates a package that can be uploaded to AYON server.
The package includes:
- Server-side code (settings, actions, API endpoints)
- Service code (list creation logic)
- Package metadata

Usage:
    python create_package.py
    python create_package.py --output /path/to/ayon-backend/addons
"""

import os
import sys
import shutil
import argparse
import logging
import zipfile
from pathlib import Path

import package

# Package info from package.py
ADDON_NAME = package.name
ADDON_VERSION = package.version

# Paths
CURRENT_ROOT = Path(__file__).parent
SERVER_ROOT = CURRENT_ROOT / "server"
SERVICES_ROOT = CURRENT_ROOT / "services"
PACKAGE_DIR = CURRENT_ROOT / "package"

# Version file content
VERSION_PY_CONTENT = f'''# -*- coding: utf-8 -*-
"""Package declaring AYON addon '{ADDON_NAME}' version."""
__version__ = "{ADDON_VERSION}"
'''

# Ignore patterns for copying
IGNORE_PATTERNS = {
    "__pycache__",
    "*.pyc",
    ".DS_Store",
    ".git",
    ".gitignore",
    ".gitkeep",
    "*.pyo",
    "*.pyd",
    ".pytest_cache",
    "*.egg-info",
}


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )


def should_ignore(path: Path) -> bool:
    """Check if path should be ignored.

    Args:
        path: Path to check.

    Returns:
        True if path should be ignored.
    """
    name = path.name
    for pattern in IGNORE_PATTERNS:
        if pattern.startswith("*"):
            if name.endswith(pattern[1:]):
                return True
        elif pattern.endswith("*"):
            if name.startswith(pattern[:-1]):
                return True
        elif name == pattern:
            return True
    return False


def copy_server_content(output_dir: Path):
    """Copy server content to output directory.

    Args:
        output_dir: Target directory for server content.
    """
    logging.info("Copying server content...")

    if not SERVER_ROOT.exists():
        logging.warning(f"Server directory not found: {SERVER_ROOT}")
        return

    for item in SERVER_ROOT.rglob("*"):
        if should_ignore(item):
            continue

        relative_path = item.relative_to(SERVER_ROOT)
        target_path = output_dir / relative_path

        if item.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target_path)
            logging.debug(f"  Copied: {relative_path}")


def create_version_file(output_dir: Path):
    """Create __version__.py file.

    Args:
        output_dir: Target directory for version file.
    """
    logging.info("Creating version file...")
    version_file = output_dir / "__version__.py"
    version_file.write_text(VERSION_PY_CONTENT)


def create_services_zip(output_dir: Path):
    """Create zip archive of services.

    Args:
        output_dir: Target directory for services zip.
    """
    logging.info("Creating services archive...")

    if not SERVICES_ROOT.exists():
        logging.warning(f"Services directory not found: {SERVICES_ROOT}")
        return

    private_dir = output_dir / "private"
    private_dir.mkdir(exist_ok=True)

    zip_path = private_dir / "services.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in SERVICES_ROOT.rglob("*"):
            if should_ignore(item):
                continue

            if item.is_file():
                relative_path = item.relative_to(SERVICES_ROOT)
                zip_file.write(item, f"services/{relative_path}")
                logging.debug(f"  Added to zip: {relative_path}")

    logging.info(f"Created: {zip_path}")


def create_final_zip(package_dir: Path) -> Path:
    """Create final zip archive of the package.

    Args:
        package_dir: Directory containing the package files.

    Returns:
        Path to the created zip file.
    """
    logging.info("Creating final package zip...")

    # Create zip in the package root (not inside the version folder)
    zip_name = f"{ADDON_NAME}-{ADDON_VERSION}.zip"
    zip_path = package_dir.parent.parent / zip_name

    # Remove existing zip if present
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in package_dir.rglob("*"):
            if item.is_file():
                # Create path relative to package root (include addon_name/version)
                relative_path = item.relative_to(package_dir.parent.parent)
                zip_file.write(item, relative_path)
                logging.debug(f"  Added to package zip: {relative_path}")

    logging.info(f"Created package zip: {zip_path}")
    return zip_path


def create_package(output_dir: Path = None, skip_services_zip: bool = False,
                   make_zip: bool = True):
    """Create AYON addon package.

    Args:
        output_dir: Custom output directory (default: ./package).
        skip_services_zip: Skip creating services.zip (for dev).
        make_zip: Create final zip archive for upload.
    """
    if output_dir is None:
        output_dir = PACKAGE_DIR / ADDON_NAME / ADDON_VERSION
    else:
        output_dir = Path(output_dir) / ADDON_NAME / ADDON_VERSION

    # Remove existing package
    if output_dir.exists():
        logging.info(f"Removing existing package: {output_dir}")
        shutil.rmtree(output_dir)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Creating package in: {output_dir}")

    # Copy server content
    copy_server_content(output_dir)

    # Create version file
    create_version_file(output_dir)

    # Create services zip
    if not skip_services_zip:
        create_services_zip(output_dir)

    # Copy package.py
    logging.info("Copying package.py...")
    shutil.copy2(CURRENT_ROOT / "package.py", output_dir / "package.py")

    # Create final zip for upload
    zip_path = None
    if make_zip:
        zip_path = create_final_zip(output_dir)

    logging.info(f"\n✓ Package created successfully!")
    logging.info(f"  Location: {output_dir}")
    logging.info(f"  Name: {ADDON_NAME}")
    logging.info(f"  Version: {ADDON_VERSION}")

    if zip_path:
        logging.info(f"  Zip file: {zip_path}")
        logging.info(f"\nYou can now:")
        logging.info(f"  1. Upload {zip_path.name} to AYON server via web UI")
        logging.info(f"  2. Or copy {output_dir} to ayon-backend/addons/")
    else:
        logging.info(f"\nYou can now:")
        logging.info(f"  1. Copy {output_dir} to ayon-backend/addons/")
        logging.info(f"  2. Or run again without --skip-zip to create upload package")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create AYON List Creator addon package"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory path (default: ./package)",
    )
    parser.add_argument(
        "--skip-services-zip",
        action="store_true",
        help="Skip creating services.zip archive (for development)",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Don't create final zip file (only create package directory)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        create_package(
            output_dir=args.output,
            skip_services_zip=args.skip_services_zip,
            make_zip=not args.no_zip,
        )
        return 0
    except Exception as e:
        logging.error(f"Failed to create package: {e}", exc_info=args.debug)
        return 1


if __name__ == "__main__":
    sys.exit(main())
