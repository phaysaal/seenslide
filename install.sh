#!/bin/bash
# SeenSlide Installation Script for Ubuntu
# This script sets up SeenSlide on a fresh Ubuntu system

set -e  # Exit on any error

echo "================================================"
echo "SeenSlide Installation Script"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Ubuntu
if [ ! -f /etc/os-release ]; then
    echo -e "${RED}Error: Cannot determine OS. This script is for Ubuntu.${NC}"
    exit 1
fi

source /etc/os-release
if [ "$ID" != "ubuntu" ]; then
    echo -e "${YELLOW}Warning: This script is designed for Ubuntu. You're running: $ID${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Install system dependencies
echo ""
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    scrot \
    xdotool \
    libx11-dev \
    libxext-dev \
    libxrandr-dev \
    libxinerama-dev \
    libxcursor-dev \
    libxi-dev

echo -e "${GREEN}✓ System dependencies installed${NC}"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Skipping.${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install SeenSlide
echo ""
echo "Installing SeenSlide..."
pip install -e .

echo -e "${GREEN}✓ SeenSlide installed${NC}"

# Create directories
echo ""
echo "Creating directories..."
mkdir -p ~/.seenslide
mkdir -p /tmp/seenslide/{images,thumbnails,db,logs}

echo -e "${GREEN}✓ Directories created${NC}"

# Copy default configuration
echo ""
echo "Setting up configuration..."
if [ -f ~/.seenslide/config.yaml ]; then
    echo -e "${YELLOW}Configuration file already exists. Skipping.${NC}"
else
    cp config/default.yaml ~/.seenslide/config.yaml
    echo -e "${GREEN}✓ Configuration copied to ~/.seenslide/config.yaml${NC}"
fi

# Create desktop entry for admin GUI
echo ""
echo "Creating desktop entry..."
cat > ~/.local/share/applications/seenslide.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SeenSlide Admin
Comment=See it again - Slide navigation for presentations
Exec=$(pwd)/venv/bin/python -m modules.admin.main
Icon=👁️
Terminal=false
Categories=Office;Presentation;
Keywords=slides;presentation;screen;capture;seenslide;seen;
EOF

echo -e "${GREEN}✓ Desktop entry created${NC}"

# Create systemd service (optional)
echo ""
read -p "Install systemd service for automatic startup? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo tee /etc/systemd/system/seenslide-server.service > /dev/null << EOF
[Unit]
Description=SeenSlide Web Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python -m modules.server.main
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable seenslide-server
    echo -e "${GREEN}✓ Systemd service installed${NC}"
    echo "  Start with: sudo systemctl start seenslide-server"
    echo "  Status: sudo systemctl status seenslide-server"
fi

# Run tests
echo ""
read -p "Run tests to verify installation? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running tests..."
    pytest tests/ -v
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed${NC}"
    else
        echo -e "${RED}✗ Some tests failed. Check output above.${NC}"
    fi
fi

# Print summary
echo ""
echo "================================================"
echo -e "${GREEN}Installation Complete!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Edit configuration: nano ~/.seenslide/config.yaml"
echo "  3. Run admin GUI: python -m modules.admin.main"
echo "  4. Run web server: python -m modules.server.main"
echo ""
echo "Documentation: $(pwd)/docs/"
echo "Configuration: ~/.seenslide/config.yaml"
echo ""
echo "For help, visit: https://github.com/yourusername/seenslide"
echo ""
echo "SeenSlide - See it again 👁️"
echo ""
