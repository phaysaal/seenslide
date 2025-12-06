# SeenSlide Admin & Management Guide

**Author:** Mahmudul Faisal Al Ameen <mahmudulfaisal@gmail.com>
**Developed with AI assistance from Claude (Anthropic)**

---

This guide covers the admin panel, user management, and complete workflow for using SeenSlide.

## Architecture Overview

SeenSlide consists of three main components:

1. **Admin Server** (Port 8081) - Management interface with authentication
2. **Viewer Server** (Port 8080) - Public slide viewing interface
3. **Capture System** - Screen capture with deduplication

## Initial Setup

### 1. First-Time Admin Setup

On the presentation PC, run the admin application for the first time:

```bash
venv_portal/bin/python seenslide_admin.py
```

This will:
- Prompt you to create the initial admin user
- Ask for username (default: admin) and password
- Password requirements:
  - At least 8 characters
  - One uppercase letter
  - One lowercase letter
  - One digit

### 2. Admin Server Ports

- **Admin Panel**: http://localhost:8081 (or http://YOUR_IP:8081)
- **Viewer**: http://localhost:8080 (or http://YOUR_IP:8080)

You can change ports with command-line arguments:

```bash
venv_portal/bin/python seenslide_admin.py --admin-port 9000 --viewer-port 8000
```

## User Management (CLI)

The `usermgr.py` tool allows local-only user management:

### Create New User

```bash
venv_portal/bin/python usermgr.py create USERNAME --email "user@example.com" --name "Full Name"
```

You'll be prompted for the password interactively.

### Change Password

```bash
venv_portal/bin/python usermgr.py passwd USERNAME
```

### List All Users

```bash
venv_portal/bin/python usermgr.py list
```

### Delete User

```bash
venv_portal/bin/python usermgr.py delete USERNAME
```

Add `--force` to skip confirmation.

### Activate/Deactivate User

```bash
venv_portal/bin/python usermgr.py activate USERNAME
venv_portal/bin/python usermgr.py deactivate USERNAME
```

## Admin Panel Workflow

### 1. Login

1. Navigate to http://YOUR_IP:8081
2. Enter your username and password
3. Click "Sign In"

### 2. Dashboard Overview

The dashboard shows three main status cards:

- **Capture Status** - Current capture session state
- **Viewer Server** - Viewer server status and port
- **Viewer Access** - QR code and URL for viewer access

### 3. Starting a Presentation

#### Option A: Start Everything Together (Recommended)

1. In the "Capture Session" section:
   - Enter **Session Name** (e.g., "Monday Tech Talk")
   - Enter **Presenter Name** (optional)
   - Select **Monitor ID** (which screen to capture)
   - Add **Description** (optional)
2. Click **"Start Capture"**

This will:
- Automatically start the viewer server (if not running)
- Start capturing slides from the selected monitor
- Make slides immediately available for viewing

#### Option B: Manual Control

1. Click **"Start Viewer"** first (in Viewer Server section)
2. Wait for viewer to start (status will show "Running")
3. Then start capture as described above

### 4. Viewing Slides (Audience)

From any device on the same network:

1. **Using QR Code**:
   - Open camera app on phone/tablet
   - Scan the QR code shown in admin dashboard
   - Opens viewer automatically

2. **Using URL**:
   - Navigate to the URL shown (e.g., http://192.168.1.140:8080)
   - Select the session from dropdown
   - View slides with navigation controls

3. **Fullscreen Mode**:
   - Click the fullscreen button (⛶) or press `F`
   - Overlay controls appear on hover:
     - Back/Forward buttons
     - Exit button (top right)
   - Press `Esc` to exit fullscreen

### 5. Stopping Capture

1. Click **"Stop Capture"** when presentation ends
   - Capture stops immediately
   - Viewer server **continues running** (audience can still browse)
2. Optionally click **"Stop Viewer"** to shut down viewer server

### 6. Managing Sessions

In the "Capture Sessions" panel:

- View all past and current sessions
- Active sessions marked with green "Active" badge
- Each session shows:
  - Presenter name
  - Number of slides
  - Status
  - Start time

#### Deleting Sessions

1. Find the session you want to delete
2. Click **"Delete"** button
3. Confirm deletion
   - **Warning**: This permanently deletes all slide images!

#### Deleting Individual Slides

Currently, individual slide deletion is available via API:

```bash
curl -X DELETE http://localhost:8081/api/sessions/{SESSION_ID}/slides/{SLIDE_ID}
```

Future UI feature will be added to the admin panel.

## Viewer Features

### Navigation

- **Keyboard Shortcuts**:
  - `←` or `Page Up` - Previous slide
  - `→` or `Page Down` or `Space` - Next slide
  - `Home` - First slide
  - `End` - Last slide
  - `L` - Toggle live mode
  - `F` - Toggle fullscreen

- **Mouse/Touch**:
  - Navigation buttons (First, Previous, Next, Last)
  - Slide number input - Jump to specific slide
  - Thumbnail grid - Click any thumbnail
  - LIVE button - Auto-jump to newest slides

### Live Mode

When enabled (green LIVE button):
- Automatically displays newest slide when captured
- Great for following along with presenter
- Disable to browse at your own pace

### Fullscreen Mode

Perfect for display on projectors or large screens:
- Clean, distraction-free view
- Overlay controls auto-hide after 3 seconds
- Mouse movement shows controls again

## WebSocket Real-Time Updates

The viewer uses WebSockets for instant updates:
- Connection status shown in header (● green = connected)
- New slides appear automatically in live mode
- Thumbnail grid updates in real-time

## Troubleshooting

### Can't login to admin panel

- Check username/password
- Ensure admin user was created during setup
- Use `usermgr.py list` to verify user exists

### Viewer not accessible from other devices

- Check firewall settings
- Ensure both devices on same network
- Try using IP address instead of hostname
- Verify viewer server is running (check admin status card)

### Capture not working

- Check monitor ID is correct
- On Wayland: Ensure portal provider is configured
- Check logs: `/tmp/server.log`
- Verify restore token in config: `dev/config_wayland.yaml`

### QR code not showing

- Ensure `qrcode` library is installed:
  ```bash
  venv_portal/bin/pip install qrcode[pil]
  ```
- Check viewer server is running

## Security Notes

1. **User Management**:
   - Only available locally via CLI
   - Cannot create/modify users via web interface
   - Prevents unauthorized account creation

2. **Session Security**:
   - Sessions expire after 24 hours
   - Logout invalidates session immediately

3. **Network**:
   - Admin panel accessible on local network only (0.0.0.0)
   - Consider firewall rules for production use

## Command Reference

### Start Admin Server

```bash
venv_portal/bin/python seenslide_admin.py \
  --admin-port 8081 \
  --viewer-port 8080 \
  --storage /tmp/seenslide
```

### Manage Users

```bash
# Create user
venv_portal/bin/python usermgr.py create admin

# Change password
venv_portal/bin/python usermgr.py passwd admin

# List users
venv_portal/bin/python usermgr.py list

# Delete user
venv_portal/bin/python usermgr.py delete olduser -f
```

### Start Viewer Only (Legacy)

```bash
venv_portal/bin/python seenslide.py server --host 0.0.0.0 --port 8080
```

## API Endpoints (for integration)

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Current user

### Session Management
- `GET /api/sessions` - List sessions
- `POST /api/sessions/start` - Start capture
- `POST /api/sessions/stop` - Stop capture
- `DELETE /api/sessions/{id}` - Delete session
- `DELETE /api/sessions/{session_id}/slides/{slide_id}` - Delete slide

### Server Control
- `POST /api/viewer/start` - Start viewer server
- `POST /api/viewer/stop` - Stop viewer server
- `GET /api/viewer/status` - Viewer status

### Utilities
- `GET /api/qr` - QR code image
- `GET /api/viewer-url` - Viewer URL info

All endpoints (except login) require authentication cookie.

## Mobile Viewing Experience

The viewer is fully optimized for smartphones and tablets:

### Mobile Features

1. **Responsive Design**:
   - Automatically adapts to screen size
   - Touch-optimized controls (minimum 44px tap targets)
   - Optimized for both portrait and landscape
   - Works on iOS, Android, and tablets

2. **Mobile-Specific Optimizations**:
   - Full-width session selector
   - Larger navigation buttons for easy tapping
   - Horizontal scrolling thumbnails
   - Optimized image sizing for mobile screens
   - Touch gestures enabled
   - Smooth scrolling

3. **Network Optimization**:
   - Efficient image loading
   - WebSocket for real-time updates
   - Works on WiFi and mobile data

### Best Practices for Mobile Viewing

**For Presenters:**
- Test QR code scanning before presentation
- Ensure stable WiFi connection
- Consider enabling live mode for audience

**For Viewers:**
- Connect to same WiFi network
- Use landscape mode for better viewing
- Enable fullscreen for immersive experience
- Use headphones if presenter has audio

### Testing Mobile View

1. **Desktop Browser (Mobile Simulation)**:
   ```
   - Open Chrome DevTools (F12)
   - Click device toolbar icon (Ctrl+Shift+M)
   - Select mobile device (iPhone, Android)
   - Test responsive layout
   ```

2. **Real Mobile Device**:
   ```
   - Scan QR code from admin panel
   - Or manually enter: http://YOUR_IP:8080
   - Test all navigation features
   - Verify touch responsiveness
   ```

## Troubleshooting

### Screen Capture Issues

If screen capture fails to start from admin panel:

1. **Verify Configuration**:
   ```bash
   cat dev/config_wayland.yaml
   ```
   Should contain valid `restore_token`.

2. **Initialize Capture Manually** (first time only):
   ```bash
   venv_portal/bin/python seenslide.py start "Test" --monitor 1
   ```
   This generates the restore token and saves to config.

3. **Check Portal Provider**:
   ```bash
   # Test portal initialization
   venv_portal/bin/python -c "
   from modules.capture.providers.portal_provider import PortalProvider
   p = PortalProvider()
   result = p.initialize({'framerate': 10})
   print('Portal OK' if result else 'Portal FAILED')
   "
   ```

4. **Check Logs**:
   ```bash
   tail -f /tmp/server.log
   ```

See `TESTING_GUIDE.md` for comprehensive troubleshooting steps.
