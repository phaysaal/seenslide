# SeenSlide Installation Guide

**Author:** Mahmudul Faisal Al Ameen <mahmudulfaisal@gmail.com>
**Developed with AI assistance from Claude (Anthropic)**

---

SeenSlide offers multiple installation methods for different use cases.

## Quick Installation (Ubuntu/Debian)

### One-Click Installer (Recommended)

The easiest way to install SeenSlide on Ubuntu or Debian:

```bash
bash install-ubuntu.sh
```

**What it does:**
- Checks system requirements
- Installs all dependencies automatically
- Sets up Python virtual environment
- Creates desktop shortcuts
- Adds command-line tools
- Creates initial admin account

**Installation takes about 2-3 minutes.**

After installation, you can:
- Launch from applications menu: Search for "SeenSlide Admin"
- Or run from terminal: `seenslide-admin`

### System Requirements

- **OS**: Ubuntu 20.04+ or Debian 11+
- **Python**: 3.9 or higher
- **RAM**: Minimum 2GB, 4GB recommended
- **Disk**: 500MB for installation + space for captured slides
- **Display**: Any (works with X11 and Wayland)

### What Gets Installed

**System packages:**
- Python 3.9+ development files
- D-Bus and GObject libraries
- Wayland portal support (if on Wayland)
- Build tools

**Python packages:**
- FastAPI & Uvicorn (web servers)
- Pillow (image processing)
- ImageHash (perceptual hashing)
- PyGObject (system integration)
- QRCode (QR generation)
- And dependencies...

**Installation locations:**
- Application: `~/.local/share/seenslide/`
- Commands: `~/.local/bin/`
- Desktop entry: `~/.local/share/applications/`
- User data: `/tmp/seenslide/` (configurable)

### Available Commands

After installation, these commands are available:

```bash
seenslide-admin      # Start admin panel (main application)
seenslide-viewer     # Start viewer server only
seenslide            # CLI interface for capture
seenslide-usermgr    # User management tool
seenslide-uninstall  # Remove SeenSlide
```

## Post-Installation

### First Run

1. **Run the admin panel:**
   ```bash
   seenslide-admin
   ```

2. **The installer already created your admin account**
   - Login with the credentials you provided during installation

3. **Access the admin panel:**
   - Open browser: http://localhost:8081
   - Or from another PC: http://YOUR_IP:8081

### Initial Configuration

For **Wayland users** (first time only):

If screen capture fails, you need to initialize the portal provider:

```bash
seenslide start "Test Session" --monitor 1
```

This will:
- Show a system permission dialog
- Generate a restore token
- Save to `dev/config_wayland.yaml`

After this, the admin panel will work normally.

### Verify Installation

Test the installation:

```bash
# Check version
seenslide --version

# List available commands
seenslide --help

# Test user management
seenslide-usermgr list
```

## Manual Installation (Advanced)

If you prefer manual control or the installer doesn't work:

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/seenslide.git
cd seenslide
```

### 2. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    libdbus-1-dev \
    libgirepository1.0-dev \
    gir1.2-gtk-3.0 \
    build-essential

# For Wayland support
sudo apt-get install -y \
    xdg-desktop-portal \
    xdg-desktop-portal-gtk
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv_portal
source venv_portal/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Create Initial Admin User

```bash
python usermgr.py create admin --name "Administrator"
```

### 6. Run Application

```bash
# Start admin panel
python seenslide_admin.py

# Or start components separately
python seenslide.py server     # Viewer server
python seenslide.py start "Session Name"  # Capture
```

## Uninstallation

### Using Uninstaller (One-Click Install)

```bash
seenslide-uninstall
```

This removes:
- Application files
- Desktop entries
- Command-line tools

**Note:** User data in `/tmp/seenslide/` is NOT removed automatically.

To remove all data:
```bash
rm -rf /tmp/seenslide
```

### Manual Uninstallation

```bash
# Remove application
rm -rf ~/.local/share/seenslide

# Remove launchers
rm -f ~/.local/bin/seenslide*

# Remove desktop entry
rm -f ~/.local/share/applications/seenslide-admin.desktop

# Remove user data (optional)
rm -rf /tmp/seenslide
```

## Updating

To update SeenSlide:

### One-Click Install Users

```bash
# Uninstall current version
seenslide-uninstall

# Download new installer
wget https://your-domain.com/install-ubuntu.sh

# Run installer
bash install-ubuntu.sh
```

**Note:** User accounts and captured slides are preserved.

### Manual Install Users

```bash
cd seenslide
git pull origin main
source venv_portal/bin/activate
pip install --upgrade -r requirements.txt
```

## Troubleshooting

### Command not found after installation

The installer adds `~/.local/bin` to your PATH in `~/.bashrc`. Either:
- Run: `source ~/.bashrc`
- Or restart your terminal

### Permission denied when running installer

Make sure the script is executable:
```bash
chmod +x install-ubuntu.sh
```

### Python version too old

SeenSlide requires Python 3.9+. On older Ubuntu:

```bash
# Add deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.10 python3.10-venv python3.10-dev

# Use python3.10 instead of python3
python3.10 -m venv venv_portal
```

### Screen capture not working (Wayland)

See "Initial Configuration" section above for Wayland setup.

### Port already in use

If ports 8080 or 8081 are in use:

```bash
seenslide-admin --admin-port 9000 --viewer-port 8888
```

## Platform Support

### Currently Supported
- ✅ Ubuntu 20.04, 22.04, 24.04
- ✅ Debian 11, 12
- ✅ Linux Mint 20+
- ✅ Pop!_OS 20.04+

### Tested Desktop Environments
- ✅ GNOME (Wayland & X11)
- ✅ KDE Plasma (Wayland & X11)
- ✅ XFCE (X11)
- ⚠️ Others may work but untested

### Coming Soon
- Windows (installer in development)
- macOS (planned)

## Getting Help

- **Documentation**: See `ADMIN_GUIDE.md` and `TESTING_GUIDE.md`
- **Issues**: Report bugs on GitHub
- **Community**: (Add your community links)

## Next Steps

After installation, see:
- `ADMIN_GUIDE.md` - Using the admin panel
- `TESTING_GUIDE.md` - Testing your setup
- `README.md` - Project overview
