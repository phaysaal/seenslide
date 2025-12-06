# SeenSlide Setup Guide

## Prerequisites

### System Requirements
- Ubuntu Linux (tested on Ubuntu 22.04+)
- Python 3.10 or higher
- Git

### Install System Dependencies

```bash
# Install Python virtual environment support
sudo apt install python3-venv python3-pip

# Install system libraries for screen capture and GUI
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    scrot \
    xdotool \
    libx11-dev \
    libxext-dev \
    libxrandr-dev \
    libxinerama-dev \
    libxcursor-dev \
    libxi-dev
```

## Installation Steps

### 1. Create Virtual Environment

```bash
# Navigate to project directory
cd /home/faisal/code/hobby/SeenSlide

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### 2. Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e ".[dev]"
```

### 3. Create Configuration

```bash
# Create user config directory
mkdir -p ~/.seenslide

# Copy default configuration
cp config/default.yaml ~/.seenslide/config.yaml

# Edit configuration as needed
nano ~/.seenslide/config.yaml
```

### 4. Create Required Directories

```bash
# Create storage directories
mkdir -p /tmp/seenslide/{images,thumbnails,db,logs}
```

### 5. Run Tests

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=modules --cov-report=html
```

## Quick Start

### Option 1: Manual Installation

Follow the steps above to set up manually.

### Option 2: Automated Installation

```bash
# Run the installation script
chmod +x install.sh
./install.sh
```

## Verification

After installation, verify everything works:

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
pytest

# Check that all modules are importable
python -c "from core.bus.event_bus import EventBus; print('EventBus imported successfully')"
python -c "from core.registry.plugin_registry import PluginRegistry; print('PluginRegistry imported successfully')"
```

## Next Steps

1. **Review Configuration**: Edit `~/.seenslide/config.yaml`
2. **Implement Modules**: Follow `dev/DEVELOPMENT_INSTRUCTIONS.md`
3. **Run the Application**: See README.md for usage instructions

## Current Implementation Status

### ✅ Completed
- [x] Project structure created
- [x] Core interfaces defined (capture, dedup, storage)
- [x] Data models created (RawCapture, ProcessedSlide, Session)
- [x] Event bus implemented
- [x] Plugin registry implemented
- [x] Configuration system created
- [x] Basic tests written

### 🚧 In Progress
- [ ] Phase 2: Capture Module
- [ ] Phase 3: Deduplication Module
- [ ] Phase 4: Storage Module
- [ ] Phase 5: Web Server
- [ ] Phase 6: Admin GUI
- [ ] Phase 7: Integration

## Troubleshooting

### Virtual Environment Creation Fails

**Error**: `ensurepip is not available`

**Solution**:
```bash
sudo apt install python3-venv
```

### Import Errors

**Error**: `ModuleNotFoundError`

**Solution**: Make sure virtual environment is activated:
```bash
source venv/bin/activate
```

### Permission Errors

**Error**: Permission denied when creating directories

**Solution**: Either use sudo or change paths in config to user-writable locations

## Development Workflow

1. Activate virtual environment: `source venv/bin/activate`
2. Make changes to code
3. Run tests: `pytest`
4. Format code: `black . && isort .`
5. Check types: `mypy .`
6. Commit changes

## Resources

- **Full Documentation**: See `dev/DEVELOPMENT_INSTRUCTIONS.md`
- **Contributing Guide**: See `CONTRIBUTING.md`
- **Configuration Reference**: See `config/default.yaml`
- **API Reference**: See `docs/` (coming soon)
