# SeenSlide

**See it again**

SeenSlide is an open-source system that allows audience members to view and navigate previously shown slides on their own devices during live presentations, while respecting the presenter's control over what has been revealed.

## Features

- 🖥️ **Automatic screen capture** - Captures presentation slides at configurable intervals
- 🔍 **Intelligent deduplication** - Filters out duplicate slides using multiple strategies
- 🌐 **Web-based viewer** - Audience accesses slides via browser (no app installation)
- 🎛️ **Admin GUI** - Easy-to-use desktop interface for organizers
- 🔌 **Modular architecture** - Pluggable components for easy customization
- 📱 **Real-time updates** - New slides appear instantly via WebSocket
- 🎨 **Presentation-agnostic** - Works with PowerPoint, Keynote, PDF, or any presentation software

## Architecture

SeenSlide uses a modular, plugin-based architecture:

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   CAPTURE    │  │    DEDUP     │  │   STORAGE    │
│   MODULE     │  │   ENGINE     │  │   MODULE     │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         │
            ┌────────────┴────────────┐
            │    EVENT BUS            │
            └────────────┬────────────┘
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
    ┌──────────────┐          ┌──────────────┐
    │  WEB SERVER  │          │  ADMIN GUI   │
    └──────────────┘          └──────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Ubuntu Linux (macOS and Windows support coming soon)
- pip package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/seenslide.git
cd seenslide

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the admin GUI
python -m modules.admin.main
```

### Basic Usage

1. **Launch Admin Panel**
   ```bash
   python -m modules.admin.main
   ```

2. **Configure Settings**
   - Select which monitor/screen to capture
   - Set capture interval (default: 2 seconds)
   - Choose deduplication strategy

3. **Start Capture**
   - Click "Start Capture" button
   - Present your slides normally

4. **Share with Audience**
   - Audience opens browser to `http://your-ip:8080`
   - They see slides as they're presented
   - Can navigate back to review previous slides

5. **Stop Capture**
   - Click "Stop Capture" when presentation ends
   - Slides remain available for review

## Configuration

Edit `config/plugins.yaml` to customize:

```yaml
capture:
  provider: "mss"
  config:
    monitor_id: 1
    interval_seconds: 2.0

deduplication:
  strategy: "hash"  # Options: hash, perceptual, hybrid
  
storage:
  provider: "filesystem"
  config:
    base_path: "/tmp/slidesync"

server:
  host: "0.0.0.0"
  port: 8080
```

## Module Overview

### Capture Module
Captures screenshots at regular intervals using various backends:
- **MSS** (default) - Fast, cross-platform screen capture
- **Scrot** - Linux native tool
- **Wayland** - For Wayland compositors (future)

### Deduplication Engine
Filters duplicate/similar slides using:
- **Hash-based** - Pixel-perfect comparison (fastest)
- **Perceptual** - Detects visual similarity (handles minor changes)
- **LLM-based** - Intelligent content comparison (future)
- **Hybrid** - Combines multiple strategies

### Storage Module
Persists slides and metadata:
- **Filesystem** - Local storage with SQLite metadata
- **S3** - Cloud storage (future)

### Web Server
FastAPI-based server with:
- REST API for slide retrieval
- WebSocket for real-time updates
- Static file serving for web client

### Admin GUI
CustomTkinter desktop application for:
- Session management
- Configuration
- Monitoring
- Control

## Development

### Project Structure

```
slidesync/
├── core/                  # Core interfaces and infrastructure
│   ├── interfaces/        # Abstract base classes
│   ├── models/           # Data models
│   ├── bus/              # Event bus
│   └── registry/         # Plugin registry
├── modules/              # Pluggable modules
│   ├── capture/          # Screen capture
│   ├── dedup/            # Deduplication
│   ├── storage/          # Storage backends
│   ├── server/           # Web server
│   └── admin/            # Admin GUI
├── config/               # Configuration files
├── tests/                # Test suite
└── docs/                 # Documentation
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_capture/test_mss_provider.py
```

### Creating a Plugin

See [docs/plugin_development.md](docs/plugin_development.md) for detailed guide.

Example:
```python
from core.interfaces.capture import ICaptureProvider

class MyCustomCapture(ICaptureProvider):
    def initialize(self, config):
        # Your initialization code
        return True
    
    def capture(self, monitor_id=None):
        # Your capture code
        return RawCapture(...)
    
    # ... implement other required methods
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Roadmap

- [x] Core architecture and interfaces
- [x] Basic capture module (MSS)
- [x] Hash-based deduplication
- [x] Filesystem storage
- [x] Web server with REST API
- [x] Admin GUI
- [ ] Perceptual deduplication
- [ ] WebSocket real-time updates
- [ ] Docker deployment
- [ ] LLM-based deduplication
- [ ] macOS support
- [ ] Windows support
- [ ] Mobile-friendly web client

## Use Cases

- **Academic Conferences** - Let attendees review complex slides
- **Corporate Training** - Participants can reference earlier material
- **Webinars** - Remote viewers navigate at their own pace
- **Workshops** - Students review instructions while working
- **Research Talks** - Audience checks detailed figures/data

## Requirements

- Python 3.10+
- 100MB disk space (more for long sessions)
- 512MB RAM (minimal)
- Network connection (for web server)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - GUI framework
- [MSS](https://github.com/BoboTiG/python-mss) - Screen capture
- [Pillow](https://python-pillow.org/) - Image processing
- [imagehash](https://github.com/JohannesBuchner/imagehash) - Perceptual hashing

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/slidesync/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/slidesync/discussions)
- **Documentation**: [docs/](docs/)

## Authors

- Your Name - Initial work

## Project Status

🚧 **In Active Development** - Currently in MVP phase

---

**Star this project on GitHub if you find it useful!** ⭐
