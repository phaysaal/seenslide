# Requirements Files

SeenSlide uses different requirements files for different environments:

## `requirements.txt` (Cloud/Production)
**For Railway deployment and cloud servers**

Minimal dependencies needed to run the cloud server:
- FastAPI & Uvicorn (web server)
- Pydantic (data models)
- Slowapi (rate limiting)
- Basic utilities

Used by:
- Railway.app deployment
- Docker containers
- Cloud hosting platforms

## `requirements-local.txt` (Development)
**For local development on desktop**

Full dependencies including:
- All cloud server dependencies
- GUI libraries (CustomTkinter)
- Screen capture (MSS, PyGObject)
- Image processing (Pillow, imagehash)
- Admin panel dependencies
- Testing tools
- Development tools

Used by:
- Local development
- Running the full desktop app
- Running tests

## Installation

### For Local Development (Desktop App)
```bash
pip install -r requirements-local.txt
```

### For Cloud Server Only
```bash
pip install -r requirements.txt
```

## Why Two Files?

The cloud server doesn't need GUI libraries, screen capture tools, or desktop-specific dependencies. Using a minimal requirements file:
- Reduces deployment size (100MB vs 500MB+)
- Faster build times (1-2 min vs 5+ min)
- Avoids dependency conflicts on cloud platforms
- Reduces security surface area
