# Packaging Guide for AYON List Creator

## Overview

This guide explains how to create and deploy the AYON List Creator addon package.

## Prerequisites

- Python 3.9 or higher
- AYON server access (for uploading the package)

## Package Structure

The addon package includes:

```
package/
└── list_creator/
    └── 1.0.0/
        ├── __init__.py           # Addon class
        ├── __version__.py        # Version info
        ├── package.py            # Package metadata
        ├── settings/             # Settings models
        ├── actions.py            # UI actions
        ├── api.py               # REST API endpoints
        └── private/
            └── services.zip      # Service code
```

## Creating a Package

### Method 1: Using create_package.py (Recommended)

Run the packaging script:

```bash
python create_package.py
```

This creates:
1. Package directory: `./package/list_creator/1.0.0/`
2. **Ready-to-upload zip file**: `./package/list_creator-1.0.0.zip`

**Options:**

```bash
# Specify custom output directory
python create_package.py --output /path/to/ayon-backend/addons

# Skip creating services.zip (for development)
python create_package.py --skip-services-zip

# Don't create final zip (only package directory)
python create_package.py --no-zip

# Enable debug logging
python create_package.py --debug
```

**Output:**
```
INFO: ✓ Package created successfully!
INFO:   Location: ./package/list_creator/1.0.0
INFO:   Name: list_creator
INFO:   Version: 1.0.0
INFO:   Zip file: ./package/list_creator-1.0.0.zip
INFO:
INFO: You can now:
INFO:   1. Upload list_creator-1.0.0.zip to AYON server via web UI
INFO:   2. Or copy ./package/list_creator/1.0.0 to ayon-backend/addons/
```

### Method 2: Manual Packaging

1. **Create directory structure:**
   ```bash
   mkdir -p package/list_creator/1.0.0
   ```

2. **Copy server files:**
   ```bash
   cp -r server/* package/list_creator/1.0.0/
   ```

3. **Copy package.py:**
   ```bash
   cp package.py package/list_creator/1.0.0/
   ```

4. **Create version file:**
   ```bash
   cat > package/list_creator/1.0.0/__version__.py << 'EOF'
   __version__ = "1.0.0"
   EOF
   ```

5. **Create services zip:**
   ```bash
   cd services
   zip -r ../package/list_creator/1.0.0/private/services.zip .
   cd ..
   ```

## Deploying the Package

### Option 1: Upload via AYON Web UI (Recommended)

1. **Create the package with zip:**
   ```bash
   python create_package.py
   ```
   This creates `package/list_creator-1.0.0.zip`

2. **Upload to AYON:**
   - Open AYON Server web UI
   - Go to **Studio Settings** → **Addons**
   - Click **Upload Addon**
   - Select `package/list_creator-1.0.0.zip`
   - Click **Upload**

3. **Activate the addon:**
   - Go to **Studio Settings** → **Addon Versions**
   - Select `list_creator` version `1.0.0`
   - Set as production/staging
   - Save changes

### Option 2: Direct Copy to Server

If you have direct access to the AYON server filesystem:

```bash
# Create package with direct output to server
python create_package.py --output /path/to/ayon-backend/addons

# Or copy manually
cp -r package/list_creator/1.0.0 /path/to/ayon-backend/addons/list_creator/
```

Then restart the AYON server.

## Package Contents Explained

### Server Files

- **`__init__.py`**: Main addon class that registers with AYON
- **`settings/`**: Pydantic models for addon settings
- **`actions.py`**: UI actions (buttons) for manual list creation
- **`api.py`**: REST API endpoints
- **`package.py`**: Metadata (name, version, services, dependencies)

### Private Files

- **`services.zip`**: Contains the service code
  - `services/processor/` - List creation service
  - Can be run as a Docker container or standalone

## Versioning

The version is defined in `package.py`:

```python
name = "list_creator"
version = "1.0.0"  # Update this for new versions
```

**Version scheme:** `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes

## Testing the Package

### 1. Validate Package Structure

```bash
python -c "
import os
import zipfile
from pathlib import Path

pkg_dir = Path('package/list_creator/1.0.0')
assert (pkg_dir / '__init__.py').exists(), 'Missing __init__.py'
assert (pkg_dir / 'package.py').exists(), 'Missing package.py'
assert (pkg_dir / 'settings/__init__.py').exists(), 'Missing settings'
print('✓ Package structure is valid')
"
```

### 2. Test Import

```bash
cd package/list_creator/1.0.0
python -c "from . import ListCreatorAddon; print('✓ Addon imports successfully')"
```

### 3. Validate Settings

```bash
cd package/list_creator/1.0.0
python -c "
from settings import ListCreatorSettings
settings = ListCreatorSettings()
print('✓ Settings model is valid')
print(f'  Default enabled: {settings.create_daily_lists.enabled}')
"
```

## Troubleshooting

### Package creation fails

- **Check Python version**: Must be 3.9+
  ```bash
  python --version
  ```

- **Check package.py exists**: Should be in root directory
  ```bash
  ls -la package.py
  ```

- **Check server/ directory exists**:
  ```bash
  ls -la server/
  ```

### Upload to AYON fails

- **Check package size**: Should be < 50MB typically
  ```bash
  du -sh package/list_creator/1.0.0
  ```

- **Check zip structure**: Should contain `list_creator/1.0.0/` directory
  ```bash
  unzip -l list_creator-1.0.0.zip | head -20
  ```

- **Check AYON server version**: Requires AYON server 1.0+

### Addon doesn't appear in AYON

1. **Check addon is uploaded**: Studio Settings → Addons
2. **Check version is set**: Studio Settings → Addon Versions
3. **Restart AYON server** if copied directly to filesystem
4. **Check server logs** for errors:
   ```bash
   tail -f /path/to/ayon/logs/server.log
   ```

## Development Workflow

For active development:

1. **Make changes** to server code or service code
2. **Test locally** (see Testing section)
3. **Create package**:
   ```bash
   python create_package.py
   ```
4. **Upload to dev/staging environment**
5. **Test in AYON**
6. **Update version** in `package.py`
7. **Create final package** and deploy to production

## Continuous Integration

Example GitHub Actions workflow for automatic packaging:

```yaml
name: Create Package

on:
  push:
    tags:
      - 'v*'

jobs:
  package:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Create package
        run: python create_package.py
      - name: Create release
        uses: actions/upload-artifact@v3
        with:
          name: list_creator-package
          path: package/
```

## Further Reading

- [AYON Addon Development](https://ayon.ynput.io/docs/dev_addon_intro)
- [README.md](README.md) - Usage guide
- [SETTINGS_GUIDE.md](SETTINGS_GUIDE.md) - Settings configuration
- [ACTIONS_GUIDE.md](ACTIONS_GUIDE.md) - Using UI actions
