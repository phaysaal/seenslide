# SeenSlide - Complete Development Instructions for Claude Code

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Implementation Phases](#implementation-phases)
6. [Core Interfaces](#core-interfaces)
7. [Data Models](#data-models)
8. [Event System](#event-system)
9. [Plugin Registry](#plugin-registry)
10. [Module Specifications](#module-specifications)
11. [Configuration System](#configuration-system)
12. [Testing Strategy](#testing-strategy)
13. [Development Guidelines](#development-guidelines)

---

## Project Overview

**Project Name:** SeenSlide

**Tagline:** See it again

**Purpose:** A modular, open-source system for real-time slide navigation during presentations. Allows audience members to view and navigate previously shown slides on their devices while the presenter maintains control.

**Key Requirements:**
- Modular, pluggable architecture
- Interface-based design (language-agnostic future)
- Event-driven communication
- Configuration-driven module selection
- Open source (MIT or Apache 2.0 license)

**Target Platform:** Linux (Ubuntu) initially, expandable to macOS/Windows

---

## Architecture

### Core Principles

1. **Separation of Concerns**: Each module handles one responsibility
2. **Loose Coupling**: Modules communicate via event bus, not direct calls
3. **High Cohesion**: Related functionality grouped in modules
4. **Plugin System**: Easy to add/replace implementations
5. **Interface-First**: Define contracts before implementation

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                   CORE INTERFACES                        │
│  (Abstract base classes defining contracts)             │
└─────────────────────────────────────────────────────────┘
            │              │              │
            ▼              ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   CAPTURE    │  │    DEDUP     │  │   STORAGE    │
│   MODULE     │  │   ENGINE     │  │   MODULE     │
└──────────────┘  └──────────────┘  └──────────────┘
            │              │              │
            └──────────────┴──────────────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │    MESSAGE BUS/QUEUE    │
            │   (Communication Layer)  │
            └─────────────────────────┘
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
    ┌──────────────┐          ┌──────────────┐
    │  WEB SERVER  │          │  ADMIN GUI   │
    │   MODULE     │          │   MODULE     │
    └──────────────┘          └──────────────┘
```

### Data Flow

```
1. Admin GUI starts session → SESSION_STARTED event
2. Capture daemon captures screen → SLIDE_CAPTURED event
3. Dedup engine receives event, compares with previous
4. If unique → SLIDE_UNIQUE event
5. Storage saves slide → SLIDE_STORED event
6. Web server receives event → pushes to WebSocket clients
7. Web clients display new slide
```

---

## Technology Stack

### Core Technologies
- **Language**: Python 3.10+
- **GUI**: CustomTkinter (modern Tkinter wrapper)
- **Web Framework**: FastAPI (async, modern, fast)
- **Screen Capture**: mss (cross-platform, fast)
- **Image Processing**: Pillow, imagehash
- **Database**: SQLite (metadata), filesystem (images)
- **Configuration**: YAML

### Key Libraries
```python
# Screen capture
mss>=9.0.1
Pillow>=10.0.0

# Deduplication
imagehash>=4.3.1

# Web server
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
websockets>=12.0

# GUI
customtkinter>=5.2.0

# Storage
sqlalchemy>=2.0.0

# Config
pyyaml>=6.0.1
python-dotenv>=1.0.0
```

---

## Project Structure

```
seenslide/
├── README.md
├── LICENSE
├── requirements.txt
├── setup.py
├── docker-compose.yml
│
├── core/
│   ├── __init__.py
│   │
│   ├── interfaces/              # Abstract base classes
│   │   ├── __init__.py
│   │   ├── capture.py           # ICaptureProvider
│   │   ├── dedup.py             # IDeduplicationStrategy
│   │   ├── storage.py           # IStorageProvider
│   │   └── events.py            # Event definitions
│   │
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── slide.py             # RawCapture, ProcessedSlide
│   │   ├── session.py           # Session
│   │   └── config.py            # Configuration models
│   │
│   ├── bus/                     # Event bus
│   │   ├── __init__.py
│   │   └── event_bus.py         # EventBus singleton
│   │
│   └── registry/                # Plugin registry
│       ├── __init__.py
│       └── plugin_registry.py   # PluginRegistry singleton
│
├── modules/
│   ├── capture/                 # Capture module
│   │   ├── __init__.py
│   │   ├── plugin.py            # Auto-registration
│   │   ├── daemon.py            # Capture daemon
│   │   └── providers/
│   │       ├── __init__.py
│   │       └── mss_provider.py  # MSS implementation
│   │
│   ├── dedup/                   # Deduplication module
│   │   ├── __init__.py
│   │   ├── plugin.py
│   │   ├── engine.py
│   │   └── strategies/
│   │       ├── __init__.py
│   │       ├── hash_strategy.py
│   │       ├── perceptual_strategy.py
│   │       └── hybrid_strategy.py
│   │
│   ├── storage/                 # Storage module
│   │   ├── __init__.py
│   │   ├── plugin.py
│   │   ├── manager.py
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── filesystem_provider.py
│   │       └── sqlite_provider.py
│   │
│   ├── server/                  # Web server
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py
│   │   │   ├── slides.py
│   │   │   └── websocket.py
│   │   └── static/
│   │       ├── index.html
│   │       ├── app.js
│   │       └── styles.css
│   │
│   └── admin/                   # Admin GUI
│       ├── __init__.py
│       ├── main.py
│       ├── gui.py
│       ├── controllers/
│       │   ├── __init__.py
│       │   └── session_controller.py
│       └── views/
│           ├── __init__.py
│           └── main_window.py
│
├── config/
│   ├── default.yaml
│   └── example.yaml
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_capture/
│   ├── test_dedup/
│   ├── test_storage/
│   └── test_integration/
│
├── docs/
│   ├── architecture.md
│   ├── api_reference.md
│   └── plugin_development.md
│
└── scripts/
    ├── install.sh
    └── run.sh
```

---

## Implementation Phases

### Phase 1: Core Foundation (Priority 1)
**Goal**: Build the foundation that everything else depends on

**Files to Create:**
1. `core/interfaces/capture.py` - ICaptureProvider interface
2. `core/interfaces/dedup.py` - IDeduplicationStrategy interface
3. `core/interfaces/storage.py` - IStorageProvider interface
4. `core/models/slide.py` - RawCapture, ProcessedSlide classes
5. `core/models/session.py` - Session class
6. `core/bus/event_bus.py` - EventBus singleton
7. `core/registry/plugin_registry.py` - PluginRegistry singleton

**Success Criteria:**
- All interfaces defined with proper docstrings
- All data models implemented
- Event bus working (pub/sub pattern)
- Plugin registry working (register/retrieve)

---

### Phase 2: Capture Module (Priority 2)
**Goal**: Implement screen capture functionality

**Files to Create:**
1. `modules/capture/providers/mss_provider.py` - MSS capture implementation
2. `modules/capture/plugin.py` - Plugin registration
3. `modules/capture/daemon.py` - Capture daemon (runs in loop)

**Implementation Details:**

**mss_provider.py** should:
- Inherit from ICaptureProvider
- Use mss library for screen capture
- Handle multiple monitors
- Return RawCapture objects
- Handle errors gracefully

**daemon.py** should:
- Run in separate thread
- Capture at configurable intervals
- Publish SLIDE_CAPTURED events
- Be start/stop-able
- Handle pause/resume

**Success Criteria:**
- Can capture screens reliably
- Events published correctly
- No memory leaks
- Configurable intervals work

---

### Phase 3: Deduplication Module (Priority 3)
**Goal**: Filter out duplicate slides

**Files to Create:**
1. `modules/dedup/strategies/hash_strategy.py` - MD5 hash comparison
2. `modules/dedup/strategies/perceptual_strategy.py` - Visual similarity
3. `modules/dedup/strategies/hybrid_strategy.py` - Combined strategies
4. `modules/dedup/plugin.py` - Plugin registration
5. `modules/dedup/engine.py` - Dedup engine

**Implementation Details:**

**hash_strategy.py**:
- Exact pixel comparison using MD5/SHA256
- Fastest method
- Returns duplicate only if 100% identical

**perceptual_strategy.py**:
- Use imagehash library (pHash)
- Compare with threshold (default 0.95)
- Handles minor differences (cursor, animations)

**hybrid_strategy.py**:
- Try hash first (fast path)
- If different, try perceptual
- Configurable pipeline

**engine.py**:
- Subscribes to SLIDE_CAPTURED events
- Compares with previous slide
- Publishes SLIDE_UNIQUE or SLIDE_DUPLICATE events
- Tracks statistics

**Success Criteria:**
- Correctly identifies duplicates
- Configurable strategies work
- Good performance (<50ms per comparison)
- Statistics tracked

---

### Phase 4: Storage Module (Priority 4)
**Goal**: Persist slides and metadata

**Files to Create:**
1. `modules/storage/providers/filesystem_provider.py` - File storage
2. `modules/storage/providers/sqlite_provider.py` - Metadata DB
3. `modules/storage/plugin.py` - Plugin registration
4. `modules/storage/manager.py` - Storage manager

**Implementation Details:**

**filesystem_provider.py**:
- Save images to disk
- Organize by session (folders)
- Generate thumbnails
- Handle file paths safely
- Return file paths

**sqlite_provider.py**:
- Create database schema
- Store session metadata
- Store slide metadata
- Implement queries
- Handle connections properly

**manager.py**:
- Subscribes to SLIDE_UNIQUE events
- Coordinates file and DB storage
- Publishes SLIDE_STORED events
- Handles cleanup

**Database Schema:**
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    name TEXT,
    start_time REAL,
    end_time REAL,
    status TEXT,
    total_slides INTEGER
);

CREATE TABLE slides (
    slide_id TEXT PRIMARY KEY,
    session_id TEXT,
    sequence_number INTEGER,
    timestamp REAL,
    image_path TEXT,
    thumbnail_path TEXT,
    width INTEGER,
    height INTEGER,
    file_size_bytes INTEGER,
    image_hash TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

**Success Criteria:**
- Slides saved reliably
- Thumbnails generated
- Database queries work
- No file path issues
- Proper error handling

---

### Phase 5: Web Server (Priority 5)
**Goal**: Serve slides to audience via HTTP/WebSocket

**Files to Create:**
1. `modules/server/app.py` - FastAPI application
2. `modules/server/routes/sessions.py` - Session endpoints
3. `modules/server/routes/slides.py` - Slide endpoints
4. `modules/server/routes/websocket.py` - WebSocket endpoint
5. `modules/server/static/index.html` - Web client
6. `modules/server/static/app.js` - Client-side JavaScript
7. `modules/server/static/styles.css` - Styling
8. `modules/server/main.py` - Entry point

**REST API Endpoints:**
```
GET  /api/v1/sessions           - List all sessions
GET  /api/v1/sessions/{id}      - Get session details
GET  /api/v1/sessions/{id}/slides - List slides in session
GET  /api/v1/slides/{id}/image  - Get slide image
GET  /api/v1/slides/{id}/thumbnail - Get thumbnail
POST /api/v1/sessions           - Create session (admin only)
```

**WebSocket Protocol:**
```json
// Client connects to: ws://host:port/ws/{session_id}

// Server sends when new slide stored:
{
  "type": "new_slide",
  "data": {
    "slide_id": "uuid",
    "sequence_number": 5,
    "thumbnail_url": "/api/v1/slides/uuid/thumbnail"
  }
}

// Server sends periodic keepalive:
{
  "type": "ping",
  "timestamp": 1234567890
}
```

**Web Client Features:**
- Grid view of slides
- Click to view full-size
- Auto-update when new slides arrive
- Navigation controls
- Responsive design

**Success Criteria:**
- REST API working
- WebSocket push working
- Web client functional
- CORS configured
- Good performance

---

### Phase 6: Admin GUI (Priority 6)
**Goal**: Desktop app for organizers to control system

**Files to Create:**
1. `modules/admin/main.py` - Entry point
2. `modules/admin/gui.py` - Main application class
3. `modules/admin/views/main_window.py` - Main window UI
4. `modules/admin/controllers/session_controller.py` - Business logic

**GUI Layout:**
```
┌─────────────────────────────────────────────┐
│  SlideSync Admin Panel                   [×]│
├─────────────────────────────────────────────┤
│                                             │
│  Session: [New Session____________] [New]  │
│                                             │
│  Monitor: [Monitor 1 ▼]                    │
│  Interval: [━━━━●━━━━━] 2 seconds          │
│  Strategy: [Hash-based ▼]                  │
│                                             │
│  Status: ● Running                          │
│  Slides Captured: 47                        │
│  Unique Slides: 45                          │
│  Server: http://192.168.1.10:8080          │
│                                             │
│  [ Start Capture ]  [ Stop Capture ]       │
│                                             │
│  Recent Activity:                           │
│  ┌─────────────────────────────────────┐   │
│  │ 14:32:15 - Slide captured           │   │
│  │ 14:32:15 - Duplicate detected       │   │
│  │ 14:32:17 - Slide captured           │   │
│  │ 14:32:17 - New slide stored (#45)   │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [Settings] [View Slides] [Help]  [Quit]   │
└─────────────────────────────────────────────┘
```

**Features:**
- Start/stop capture
- Monitor selection
- Configuration
- Live statistics
- Activity log
- Settings window

**Implementation with CustomTkinter:**
```python
import customtkinter as ctk

class AdminGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SlideSync Admin")
        self.geometry("800x600")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create widgets
        self.create_widgets()
        
        # Subscribe to events
        self.setup_event_handlers()
    
    def create_widgets(self):
        # Title
        self.title_label = ctk.CTkLabel(
            self, 
            text="SlideSync Admin Panel",
            font=("Arial", 24, "bold")
        )
        self.title_label.pack(pady=20)
        
        # Monitor selection
        # ... more widgets ...
        
    def start_capture(self):
        # Start capture daemon
        pass
```

**Success Criteria:**
- Professional appearance
- All controls working
- Real-time updates
- Responsive UI
- Error handling

---

### Phase 7: Integration (Priority 7)
**Goal**: Make all modules work together

**Files to Create:**
1. `main.py` - Main orchestrator
2. `config.py` - Configuration loader

**main.py Responsibilities:**
- Load configuration
- Initialize all modules
- Start event bus
- Handle graceful shutdown
- Coordinate components

**Example Structure:**
```python
class SlideSync:
    def __init__(self, config_path):
        self.config = load_config(config_path)
        self.event_bus = EventBus()
        self.registry = PluginRegistry()
        
        # Import plugins (auto-registers)
        import modules.capture.plugin
        import modules.dedup.plugin
        import modules.storage.plugin
        
        # Initialize components
        self.capture = self.init_capture()
        self.dedup = self.init_dedup()
        self.storage = self.init_storage()
        self.server = self.init_server()
        
    def start(self):
        # Start all services
        pass
    
    def stop(self):
        # Graceful shutdown
        pass
```

**Success Criteria:**
- All modules integrated
- Configuration working
- End-to-end flow works
- No integration bugs

---

## Core Interfaces

### ICaptureProvider Interface

```python
# core/interfaces/capture.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from core.models.slide import RawCapture

class ICaptureProvider(ABC):
    """Interface for screen capture providers"""
    
    @abstractmethod
    def initialize(self, config: dict) -> bool:
        """Initialize the capture provider with configuration"""
        pass
    
    @abstractmethod
    def list_monitors(self) -> List[Dict]:
        """List available monitors/screens
        
        Returns:
            List of dicts: [{"id": 1, "x": 0, "y": 0, "width": 1920, "height": 1080}]
        """
        pass
    
    @abstractmethod
    def capture(self, monitor_id: Optional[int] = None) -> RawCapture:
        """Capture a screenshot
        
        Args:
            monitor_id: Monitor to capture (None = primary)
            
        Returns:
            RawCapture object
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
    
    @property
    @abstractmethod
    def supported_platforms(self) -> List[str]:
        """List of supported platforms: ["linux", "darwin", "win32"]"""
        pass
```

### IDeduplicationStrategy Interface

```python
# core/interfaces/dedup.py
from abc import ABC, abstractmethod
from core.models.slide import RawCapture

class IDeduplicationStrategy(ABC):
    """Interface for deduplication strategies"""
    
    @abstractmethod
    def initialize(self, config: dict) -> bool:
        """Initialize the strategy with configuration"""
        pass
    
    @abstractmethod
    def is_duplicate(self, current: RawCapture, previous: RawCapture) -> bool:
        """Check if current is duplicate of previous
        
        Args:
            current: Current capture
            previous: Previous capture
            
        Returns:
            True if duplicate, False if unique
        """
        pass
    
    @abstractmethod
    def get_similarity_score(self) -> float:
        """Get similarity score from last comparison
        
        Returns:
            Float 0.0-1.0 (0=different, 1=identical)
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name"""
        pass
    
    @property
    @abstractmethod
    def avg_processing_time_ms(self) -> float:
        """Average processing time in milliseconds"""
        pass
```

### IStorageProvider Interface

```python
# core/interfaces/storage.py
from abc import ABC, abstractmethod
from typing import Optional, List
from core.models.slide import ProcessedSlide
from core.models.session import Session

class IStorageProvider(ABC):
    """Interface for storage providers"""
    
    @abstractmethod
    def initialize(self, config: dict) -> bool:
        """Initialize storage provider"""
        pass
    
    @abstractmethod
    def create_session(self, session: Session) -> str:
        """Create a new session
        
        Returns:
            Session ID (UUID)
        """
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve session by ID"""
        pass
    
    @abstractmethod
    def save_slide(self, slide: ProcessedSlide) -> str:
        """Save a processed slide
        
        Returns:
            Slide ID (UUID)
        """
        pass
    
    @abstractmethod
    def get_slide(self, slide_id: str) -> Optional[ProcessedSlide]:
        """Retrieve slide by ID"""
        pass
    
    @abstractmethod
    def list_slides(
        self, 
        session_id: str, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ProcessedSlide]:
        """List slides for a session"""
        pass
    
    @abstractmethod
    def get_slide_count(self, session_id: str) -> int:
        """Get total slide count for session"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
```

---

## Data Models

### RawCapture Model

```python
# core/models/slide.py
from dataclasses import dataclass, field
from PIL import Image
import uuid

@dataclass
class RawCapture:
    """Raw captured screenshot before processing"""
    image: Image.Image              # PIL Image object
    timestamp: float                # Unix timestamp
    monitor_id: int                 # Which monitor
    width: int                      # Image width in pixels
    height: int                     # Image height in pixels
    capture_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = field(default_factory=dict)
```

### ProcessedSlide Model

```python
@dataclass
class ProcessedSlide:
    """Processed slide after deduplication"""
    slide_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    image_path: str = ""            # Path to saved image
    thumbnail_path: str = ""        # Path to thumbnail
    timestamp: float = 0.0          # Unix timestamp
    sequence_number: int = 0        # Order in session
    width: int = 0
    height: int = 0
    file_size_bytes: int = 0
    image_hash: str = ""            # For quick comparison
    similarity_score: float = 0.0   # vs previous slide
    metadata: dict = field(default_factory=dict)
```

### Session Model

```python
# core/models/session.py
from dataclasses import dataclass, field
from typing import Optional
import uuid

@dataclass
class Session:
    """Represents a presentation session"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    presenter_name: str = ""
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    status: str = "created"  # created, active, paused, completed
    total_slides: int = 0
    capture_interval_seconds: float = 2.0
    dedup_strategy: str = "hash"
    metadata: dict = field(default_factory=dict)
    
    def is_active(self) -> bool:
        return self.status == "active"
    
    def duration_seconds(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
```

---

## Event System

### Event Types

```python
# core/bus/event_bus.py
from enum import Enum

class EventType(Enum):
    # Session events
    SESSION_CREATED = "session.created"
    SESSION_STARTED = "session.started"
    SESSION_PAUSED = "session.paused"
    SESSION_STOPPED = "session.stopped"
    
    # Capture events
    SLIDE_CAPTURED = "slide.captured"
    CAPTURE_FAILED = "capture.failed"
    
    # Dedup events
    SLIDE_DUPLICATE = "slide.duplicate"
    SLIDE_UNIQUE = "slide.unique"
    
    # Storage events
    SLIDE_STORED = "slide.stored"
    STORAGE_ERROR = "storage.error"
    
    # Server events
    CLIENT_CONNECTED = "client.connected"
    
    # Error events
    ERROR_OCCURRED = "error.occurred"
```

### Event Class

```python
@dataclass
class Event:
    """Represents an event in the system"""
    type: EventType
    data: dict
    timestamp: float = None
    source: str = "unknown"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
```

### EventBus Implementation

```python
class EventBus:
    """Singleton event bus for pub/sub communication"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._subscribers = {}
        self._event_history = []
        self._initialized = True
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe a handler to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def publish(self, event: Event):
        """Publish an event to all subscribers"""
        self._event_history.append(event)
        if event.type in self._subscribers:
            for handler in self._subscribers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    logging.error(f"Error in handler: {e}")
```

---

## Plugin Registry

```python
# core/registry/plugin_registry.py
class PluginRegistry:
    """Singleton registry for all plugin types"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._capture_providers = {}
        self._dedup_strategies = {}
        self._storage_providers = {}
        self._initialized = True
    
    def register_capture_provider(self, name: str, provider_class):
        """Register a capture provider"""
        self._capture_providers[name] = provider_class
    
    def get_capture_provider(self, name: str):
        """Get a capture provider by name"""
        return self._capture_providers.get(name)
    
    def list_capture_providers(self) -> List[str]:
        """List all registered providers"""
        return list(self._capture_providers.keys())
    
    # Similar methods for dedup and storage...
```

---

## Configuration System

### Loading Configuration

```python
# config.py
import yaml
from pathlib import Path

def load_config(config_path: str = "config/default.yaml") -> dict:
    """Load configuration from YAML file"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required fields
    validate_config(config)
    
    return config

def validate_config(config: dict):
    """Validate configuration has required fields"""
    required = ['capture', 'deduplication', 'storage', 'server']
    for field in required:
        if field not in config:
            raise ValueError(f"Missing required config: {field}")
```

---

## Testing Strategy

### Unit Tests

Test each component in isolation:

```python
# tests/test_capture/test_mss_provider.py
import pytest
from modules.capture.providers.mss_provider import MSSCaptureProvider

def test_provider_initialization():
    provider = MSSCaptureProvider()
    assert provider.initialize({}) == True
    assert provider.name == "mss"

def test_list_monitors():
    provider = MSSCaptureProvider()
    provider.initialize({})
    monitors = provider.list_monitors()
    assert len(monitors) > 0
    assert "id" in monitors[0]
    assert "width" in monitors[0]

def test_capture():
    provider = MSSCaptureProvider()
    provider.initialize({})
    capture = provider.capture()
    assert capture.image is not None
    assert capture.width > 0
    assert capture.height > 0
```

### Integration Tests

Test components working together:

```python
# tests/test_integration/test_capture_to_storage.py
def test_full_pipeline():
    # Setup
    event_bus = EventBus()
    capture = MSSCaptureProvider()
    dedup = HashDeduplicationStrategy()
    storage = FilesystemStorageProvider()
    
    # Initialize
    capture.initialize({})
    dedup.initialize({})
    storage.initialize({"base_path": "/tmp/test"})
    
    # Capture
    raw1 = capture.capture()
    raw2 = capture.capture()
    
    # Dedup
    is_dup = dedup.is_duplicate(raw2, raw1)
    assert is_dup == True  # Same screen should be duplicate
    
    # Storage (only store unique)
    if not is_dup:
        slide = ProcessedSlide(...)
        slide_id = storage.save_slide(slide)
        assert slide_id is not None
```

---

## Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints everywhere
- Write docstrings for all public functions
- Maximum line length: 100 characters
- Use meaningful variable names

### Error Handling
- Use specific exceptions
- Always log errors with context
- Fail gracefully
- Provide helpful error messages

### Logging
- Use Python's logging module
- Log at appropriate levels
- Include context in messages
- Don't log sensitive data

### Performance
- Capture at reasonable intervals (2-5s)
- Generate thumbnails async
- Cache frequently accessed data
- Profile for bottlenecks

### Security
- Validate all user inputs
- Use environment variables for secrets
- Don't commit API keys
- Sanitize file paths
- Implement rate limiting

---

## Critical Implementation Notes

### 1. Thread Safety
- EventBus must be thread-safe
- Use locks for shared data
- Capture daemon runs in separate thread

### 2. Resource Management
- Always cleanup in `__del__` or context managers
- Close file handles
- Release screen capture resources
- Close database connections

### 3. Plugin Auto-Registration Pattern

```python
# modules/capture/plugin.py
from core.registry import PluginRegistry
from .providers.mss_provider import MSSCaptureProvider

def register():
    registry = PluginRegistry()
    registry.register_capture_provider("mss", MSSCaptureProvider)

# Auto-register on import
register()
```

### 4. Configuration Loading
- Load config at startup
- Validate all values
- Provide sensible defaults
- Allow environment overrides

---

## Success Criteria

### MVP Checklist
- [ ] Can capture slides automatically
- [ ] Can filter duplicates
- [ ] Can view slides in browser
- [ ] Has working admin GUI
- [ ] Configuration via YAML
- [ ] Runs on Ubuntu
- [ ] Basic documentation

### Version 1.0 Checklist
- [ ] All MVP features
- [ ] Multiple dedup strategies
- [ ] Thumbnail generation
- [ ] WebSocket real-time updates
- [ ] Professional UI
- [ ] Docker deployment
- [ ] >80% test coverage
- [ ] Complete documentation
- [ ] GitHub release

---

## Getting Started

### Initial Setup

```bash
# Create project directory
mkdir slidesync
cd slidesync

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create directory structure
mkdir -p core/{interfaces,models,bus,registry}
mkdir -p modules/{capture,dedup,storage,server,admin}
mkdir -p config tests docs
```

### Development Order

1. **Start with core/** - Interfaces, models, event bus, registry
2. **Then modules/capture/** - Screen capture working
3. **Then modules/dedup/** - Deduplication working
4. **Then modules/storage/** - Persistence working
5. **Then modules/server/** - Web server working
6. **Then modules/admin/** - GUI working
7. **Finally integration** - Everything together

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific module tests
pytest tests/test_capture/
```

---

## Common Pitfalls to Avoid

1. **Circular imports** - Use type hints with strings
2. **Global state** - Use singletons carefully
3. **Blocking operations** - Use async/threading for I/O
4. **Memory leaks** - Don't store full images in memory
5. **Hard-coded paths** - Always use configuration
6. **Missing error handling** - Wrap external calls
7. **Poor naming** - Use descriptive names
8. **Missing docs** - Document all public APIs
9. **Tight coupling** - Use interfaces, not implementations
10. **No logging** - Add logging at key points

---

## Questions & Decisions

### Resolved
- ✅ Language: Python
- ✅ GUI: CustomTkinter
- ✅ Server: FastAPI
- ✅ Capture: mss
- ✅ Storage: SQLite + filesystem

### To Consider
- Should capture daemon be separate process? (Start with thread)
- Support multiple sessions simultaneously? (Not in MVP)
- How to handle very long presentations? (Pagination)
- Image format: PNG or JPEG? (PNG for quality, configurable)
- Encrypt stored slides? (Not in MVP)

---

## Final Notes

This is a well-architected project with:
- Clean separation of concerns
- Modular, pluggable design
- Clear interfaces
- Event-driven communication
- Easy to test
- Easy to extend

**Remember**: Working software over perfect architecture.

Start simple, then refactor as needed.

Focus on getting MVP working first, then polish and add features.

---

**Document Version:** 1.0  
**Created:** 2024-12-03  
**For:** Claude Code Development  
**Estimated Timeline:** 4-5 weeks for v1.0
