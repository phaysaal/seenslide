#!/bin/bash
#
# SeenSlide Installer for Ubuntu/Debian
# One-click installation script
#
# Author: Mahmudul Faisal Al Ameen <mahmudulfaisal@gmail.com>
# Developed with AI assistance from Claude (Anthropic)
# Copyright (c) 2024 Mahmudul Faisal Al Ameen
#
# Usage: curl -fsSL https://your-domain.com/install.sh | bash
# Or: wget -qO- https://your-domain.com/install.sh | bash
# Or: bash install-ubuntu.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/.local/share/seenslide"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons"
VERSION="1.0.0"

# GitHub repository (change this to your actual repo)
GITHUB_REPO="https://github.com/yourusername/seenslide"
DOWNLOAD_URL="https://github.com/yourusername/seenslide/archive/refs/heads/main.zip"

# Print functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${GREEN}=====================================${NC}"
    echo -e "${GREEN}  SeenSlide Installer v${VERSION}${NC}"
    echo -e "${GREEN}=====================================${NC}"
    echo ""
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root"
        print_info "Please run as a regular user (sudo will be requested when needed)"
        exit 1
    fi
}

# Check Ubuntu/Debian
check_os() {
    if [[ ! -f /etc/os-release ]]; then
        print_error "Cannot detect OS. This installer is for Ubuntu/Debian only."
        exit 1
    fi

    source /etc/os-release
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        print_warning "This installer is designed for Ubuntu/Debian."
        print_warning "Detected OS: $ID $VERSION_ID"
        read -p "Do you want to continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    print_info "Detected: $PRETTY_NAME"
}

# Check system requirements
check_requirements() {
    print_info "Checking system requirements..."

    # Check for required commands
    local missing_cmds=()

    for cmd in wget curl unzip python3; do
        if ! command -v $cmd &> /dev/null; then
            missing_cmds+=($cmd)
        fi
    done

    if [ ${#missing_cmds[@]} -gt 0 ]; then
        print_warning "Missing required commands: ${missing_cmds[*]}"
        print_info "Installing required packages..."
        sudo apt-get update -qq
        sudo apt-get install -y -qq wget curl unzip python3 python3-pip python3-venv
    fi

    # Check Python version
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 9 ]]; then
        print_error "Python 3.9 or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi

    print_success "Python $PYTHON_VERSION detected"
}

# Install system dependencies
install_dependencies() {
    print_info "Installing system dependencies..."

    # List of required packages
    local packages=(
        "python3-dev"
        "python3-pip"
        "python3-venv"
        "libdbus-1-dev"
        "libgirepository1.0-dev"
        "gir1.2-gtk-3.0"
        "build-essential"
    )

    # Wayland portal support
    if [[ "$XDG_SESSION_TYPE" == "wayland" ]]; then
        print_info "Wayland session detected, installing portal support..."
        packages+=(
            "xdg-desktop-portal"
            "xdg-desktop-portal-gtk"
        )
    fi

    print_info "Installing packages: ${packages[*]}"
    sudo apt-get update -qq
    sudo apt-get install -y -qq "${packages[@]}"

    print_success "System dependencies installed"
}

# Download or copy application
download_application() {
    print_info "Setting up SeenSlide..."

    # Create install directory
    mkdir -p "$INSTALL_DIR"

    # If running from source directory, copy files
    if [[ -f "seenslide.py" && -d "modules" ]]; then
        print_info "Installing from source directory..."
        cp -r . "$INSTALL_DIR/"
        cd "$INSTALL_DIR"
    else
        # Download from GitHub
        print_info "Downloading SeenSlide..."
        cd "$INSTALL_DIR"

        # Using wget or curl to download
        if command -v wget &> /dev/null; then
            wget -q --show-progress -O seenslide.zip "$DOWNLOAD_URL"
        else
            curl -L -o seenslide.zip "$DOWNLOAD_URL"
        fi

        print_info "Extracting files..."
        unzip -q seenslide.zip

        # Move files from extracted directory
        EXTRACT_DIR=$(unzip -l seenslide.zip | head -4 | tail -1 | awk '{print $4}' | cut -d'/' -f1)
        if [[ -d "$EXTRACT_DIR" ]]; then
            mv "$EXTRACT_DIR"/* .
            rm -rf "$EXTRACT_DIR"
        fi

        rm seenslide.zip
    fi

    print_success "Application files ready"
}

# Setup Python virtual environment
setup_virtualenv() {
    print_info "Creating Python virtual environment..."

    cd "$INSTALL_DIR"
    python3 -m venv venv_portal

    print_info "Installing Python dependencies..."
    source venv_portal/bin/activate

    # Upgrade pip
    pip install -q --upgrade pip

    # Install requirements
    if [[ -f "requirements.txt" ]]; then
        pip install -q -r requirements.txt
    else
        # Install essential packages
        pip install -q fastapi uvicorn Pillow PyYAML imagehash pydbus PyGObject qrcode[pil]
    fi

    deactivate

    print_success "Virtual environment created"
}

# Create launcher scripts
create_launchers() {
    print_info "Creating launcher scripts..."

    mkdir -p "$BIN_DIR"

    # Create seenslide-admin launcher
    cat > "$BIN_DIR/seenslide-admin" << 'EOF'
#!/bin/bash
INSTALL_DIR="$HOME/.local/share/seenslide"
cd "$INSTALL_DIR"
source venv_portal/bin/activate
python seenslide_admin.py "$@"
EOF

    chmod +x "$BIN_DIR/seenslide-admin"

    # Create seenslide CLI launcher
    cat > "$BIN_DIR/seenslide" << 'EOF'
#!/bin/bash
INSTALL_DIR="$HOME/.local/share/seenslide"
cd "$INSTALL_DIR"
source venv_portal/bin/activate
python seenslide.py "$@"
EOF

    chmod +x "$BIN_DIR/seenslide"

    # Create seenslide-viewer launcher
    cat > "$BIN_DIR/seenslide-viewer" << 'EOF'
#!/bin/bash
INSTALL_DIR="$HOME/.local/share/seenslide"
cd "$INSTALL_DIR"
source venv_portal/bin/activate
python seenslide.py server "$@"
EOF

    chmod +x "$BIN_DIR/seenslide-viewer"

    # Create user manager launcher
    cat > "$BIN_DIR/seenslide-usermgr" << 'EOF'
#!/bin/bash
INSTALL_DIR="$HOME/.local/share/seenslide"
cd "$INSTALL_DIR"
source venv_portal/bin/activate
python usermgr.py "$@"
EOF

    chmod +x "$BIN_DIR/seenslide-usermgr"

    print_success "Launcher scripts created in $BIN_DIR"
}

# Create desktop entry
create_desktop_entry() {
    print_info "Creating desktop entry..."

    mkdir -p "$DESKTOP_DIR"
    mkdir -p "$ICON_DIR"

    # Create a simple icon (you can replace this with actual icon)
    # For now, we'll skip icon creation

    # Create desktop file
    cat > "$DESKTOP_DIR/seenslide-admin.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SeenSlide Admin
Comment=Presentation Capture & Sharing Tool
Exec=$BIN_DIR/seenslide-admin
Terminal=false
Categories=Office;Presentation;
Keywords=presentation;capture;slides;
StartupNotify=true
EOF

    chmod +x "$DESKTOP_DIR/seenslide-admin.desktop"

    print_success "Desktop entry created"
}

# Add to PATH if needed
setup_path() {
    # Check if BIN_DIR is in PATH
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        print_info "Adding $BIN_DIR to PATH..."

        # Add to .bashrc
        if [[ -f "$HOME/.bashrc" ]]; then
            echo "" >> "$HOME/.bashrc"
            echo "# SeenSlide" >> "$HOME/.bashrc"
            echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$HOME/.bashrc"
        fi

        # Add to .zshrc if exists
        if [[ -f "$HOME/.zshrc" ]]; then
            echo "" >> "$HOME/.zshrc"
            echo "# SeenSlide" >> "$HOME/.zshrc"
            echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$HOME/.zshrc"
        fi

        print_warning "PATH updated. Please run: source ~/.bashrc"
        print_warning "Or restart your terminal for changes to take effect"
    fi
}

# Initial setup (create admin user)
initial_setup() {
    print_info "Running initial setup..."

    cd "$INSTALL_DIR"
    source venv_portal/bin/activate

    # Check if users already exist
    if python -c "from modules.storage.user_storage import UserStorage; import sys; storage = UserStorage(); storage.initialize({'base_path': '/tmp/seenslide'}); users = storage.get_all_users(); sys.exit(0 if len(users) > 0 else 1)" 2>/dev/null; then
        print_info "Admin user already exists, skipping initial setup"
    else
        print_info ""
        print_info "Let's create your admin account..."
        python usermgr.py create admin --name "Administrator"
    fi

    deactivate
}

# Create uninstaller
create_uninstaller() {
    cat > "$BIN_DIR/seenslide-uninstall" << 'UNINSTALL_EOF'
#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}SeenSlide Uninstaller${NC}"
echo ""
read -p "Are you sure you want to uninstall SeenSlide? (y/N) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled"
    exit 0
fi

echo -e "${RED}Uninstalling SeenSlide...${NC}"

# Remove application directory
rm -rf "$HOME/.local/share/seenslide"

# Remove launchers
rm -f "$HOME/.local/bin/seenslide"
rm -f "$HOME/.local/bin/seenslide-admin"
rm -f "$HOME/.local/bin/seenslide-viewer"
rm -f "$HOME/.local/bin/seenslide-usermgr"
rm -f "$HOME/.local/bin/seenslide-uninstall"

# Remove desktop entry
rm -f "$HOME/.local/share/applications/seenslide-admin.desktop"

# Note about data
echo ""
echo -e "${YELLOW}Note:${NC} User data in /tmp/seenslide was NOT removed."
echo "To remove all data including captured slides, run:"
echo "  rm -rf /tmp/seenslide"
echo ""

# Note about PATH
echo -e "${YELLOW}Note:${NC} PATH modifications in ~/.bashrc or ~/.zshrc were NOT removed."
echo "You may want to manually remove the SeenSlide section from these files."
echo ""

echo -e "${GREEN}SeenSlide has been uninstalled.${NC}"
UNINSTALL_EOF

    chmod +x "$BIN_DIR/seenslide-uninstall"
}

# Print completion message
print_completion() {
    echo ""
    echo -e "${GREEN}=====================================${NC}"
    echo -e "${GREEN}  Installation Complete!${NC}"
    echo -e "${GREEN}=====================================${NC}"
    echo ""
    print_info "SeenSlide has been installed to: $INSTALL_DIR"
    echo ""
    echo -e "${BLUE}Available commands:${NC}"
    echo "  seenslide-admin      - Start admin panel"
    echo "  seenslide-viewer     - Start viewer server only"
    echo "  seenslide            - CLI interface"
    echo "  seenslide-usermgr    - Manage users"
    echo "  seenslide-uninstall  - Remove SeenSlide"
    echo ""
    echo -e "${BLUE}Quick Start:${NC}"
    echo "  1. Run: seenslide-admin"
    echo "  2. Login with the admin account you created"
    echo "  3. Start capturing presentations!"
    echo ""
    echo -e "${BLUE}Desktop App:${NC}"
    echo "  Search for 'SeenSlide Admin' in your application menu"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "  Admin Guide: $INSTALL_DIR/ADMIN_GUIDE.md"
    echo "  Testing Guide: $INSTALL_DIR/TESTING_GUIDE.md"
    echo ""
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo -e "${YELLOW}Important:${NC} Run 'source ~/.bashrc' or restart your terminal"
    fi
    echo ""
}

# Main installation flow
main() {
    print_header

    check_root
    check_os
    check_requirements
    install_dependencies
    download_application
    setup_virtualenv
    create_launchers
    create_desktop_entry
    setup_path
    create_uninstaller
    initial_setup

    print_completion
}

# Run main installation
main
