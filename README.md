# SeenSlide

**Real-time Presentation Capture & Sharing**

Share your presentation slides instantly with your audience. Capture slides automatically as you present, and let viewers follow along on their phones or tablets via a simple QR code.

Perfect for conferences, classrooms, training sessions, and webinars.

---

## ✨ Features

### For Presenters
- 🎯 **One-Click Installation** - Ubuntu installer sets up everything automatically
- 🔐 **Secure Admin Panel** - Web-based control center with authentication
- 📊 **Smart Capture** - Automatic screen capture with intelligent deduplication
- 🎚️ **Adjustable Sensitivity** - Fine-tune how strict duplicate detection is
- 📱 **QR Code Sharing** - Instant audience access via QR code
- 🖥️ **Wayland Support** - Works with modern Linux desktop environments

### For Viewers
- 📱 **Mobile Optimized** - Perfect viewing on phones and tablets
- 🔄 **Live Mode** - Auto-jump to latest slides as they appear
- 🔍 **Zoom & Pan** - Pinch to zoom on touch devices
- ⛶ **Fullscreen Mode** - Immersive viewing with side navigation
- ⬅️➡️ **Full Navigation** - Browse slides at your own pace
- 🌐 **No App Required** - Works in any web browser

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

## 🚀 Quick Start

### One-Click Installation (Ubuntu/Debian)

```bash
# Download and run the installer
wget https://raw.githubusercontent.com/phaysaal/seenslide/main/install-ubuntu.sh
bash install-ubuntu.sh
```

That's it! The installer will:
- ✅ Install all dependencies
- ✅ Set up the application
- ✅ Create your admin account
- ✅ Add desktop shortcuts

**Time:** 2-3 minutes

### Launch SeenSlide

**From Desktop:**
- Search for "SeenSlide Admin" in applications menu

**From Terminal:**
```bash
seenslide-admin
```

**Then:**
1. Open browser: `http://localhost:8081`
2. Login with your credentials
3. Click "Start Capture"
4. Show QR code to audience

**Viewers access at:** `http://YOUR_IP:8080`

### System Requirements

- **OS**: Ubuntu 20.04+ or Debian 11+
- **Python**: 3.9 or higher
- **RAM**: 4GB recommended
- **Display**: X11 or Wayland

## Configuration

SeenSlide is configured primarily through the **Admin Panel** web interface:

- **Deduplication Tolerance**: Adjustable slider (0-100%) controls how strictly duplicates are filtered
  - 0-80%: Detect small changes (10-50% of screen)
  - 80-95%: Detect medium changes (50-90% of screen)
  - 95-100%: Only detect complete window changes

- **Monitor Selection**: Choose which display to capture
- **Capture Interval**: Configured in session settings

Advanced users can edit `config/plugins.yaml` for low-level settings:

```yaml
capture:
  provider: "portal"  # Uses XDG Desktop Portal for Wayland
  config:
    framerate: 10
    cursor_mode: "hidden"

deduplication:
  strategy: "perceptual"
  perceptual_threshold: 0.50

storage:
  provider: "filesystem"
  config:
    base_path: "/tmp/seenslide"
```

## Module Overview

### Capture Module
Captures screenshots at configurable intervals:
- **XDG Desktop Portal** (default) - Wayland-native screen capture via PipeWire
- **MSS** - Fallback for X11 systems
- Automatic permission handling with restore tokens

### Deduplication Engine
Filters duplicate/similar slides using:
- **Perceptual Hashing** - Detects visual similarity with configurable tolerance
- **Hash-based** - Pixel-perfect comparison for exact duplicates
- **Hybrid** - Combines multiple strategies for optimal results
- Adjustable sensitivity via admin panel slider

### Storage Module
Persists slides and metadata:
- **Filesystem** - Local storage with organized session directories
- **SQLite** - User accounts and session metadata
- Automatic cleanup and session deletion

### Viewer Server
FastAPI-based server (port 8080) with:
- REST API for slide retrieval
- WebSocket for real-time updates with polling fallback
- Mobile-optimized responsive web interface
- Fullscreen mode with touch support
- Zoom and pan functionality

### Admin Server
FastAPI-based control panel (port 8081) with:
- Secure authentication with session management
- Capture and viewer server control
- QR code generation for easy sharing
- Real-time status monitoring
- Session and slide management

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

**Completed (v1.0 Beta):**
- [x] Core architecture and interfaces
- [x] XDG Desktop Portal capture (Wayland support)
- [x] MSS capture provider (X11 fallback)
- [x] Perceptual hash deduplication with adjustable tolerance
- [x] Hash-based deduplication
- [x] Filesystem storage with SQLite
- [x] Web server with REST API
- [x] WebSocket real-time updates + polling fallback
- [x] Admin web panel with authentication
- [x] Mobile-optimized viewer interface
- [x] Fullscreen mode with touch controls
- [x] Zoom and pan functionality
- [x] QR code sharing
- [x] Session management
- [x] One-click Ubuntu installer

**Planned for Future Releases:**
- [ ] Docker deployment
- [ ] LLM-based deduplication
- [ ] Cloud storage (S3) support
- [ ] macOS installer and support
- [ ] Windows installer and support
- [ ] Multi-presenter sessions
- [ ] Annotation tools
- [ ] PDF export

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

- **Issues**: [GitHub Issues](https://github.com/phaysaal/seenslide/issues)
- **Discussions**: [GitHub Discussions](https://github.com/phaysaal/seenslide/discussions)
- **Documentation**: See [ADMIN_GUIDE.md](ADMIN_GUIDE.md), [TESTING_GUIDE.md](TESTING_GUIDE.md), and [INSTALL.md](INSTALL.md)

## Author

**Mahmudul Faisal Al Ameen**
- Email: mahmudulfaisal@gmail.com
- GitHub: [@phaysaal](https://github.com/phaysaal)

### Development

This project was developed with AI pair programming assistance from **Claude (Anthropic)**. The architecture, features, and implementation were designed and directed by Mahmudul Faisal Al Ameen, with Claude providing code generation, debugging assistance, and technical suggestions.

## Project Status

🚧 **In Active Development** - Currently in MVP phase

## Copyright

Copyright (c) 2024 Mahmudul Faisal Al Ameen

---

**Star this project on GitHub if you find it useful!** ⭐
