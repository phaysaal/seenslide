# SeenSlide Testing & Troubleshooting Guide

**Author:** Mahmudul Faisal Al Ameen <mahmudulfaisal@gmail.com>
**Developed with AI assistance from Claude (Anthropic)**

---

This guide helps you test and troubleshoot SeenSlide components.

## Quick Test Checklist

### 1. Test User Management (CLI)

```bash
# Create initial admin user
venv_portal/bin/python usermgr.py create testadmin --name "Test Admin"
# Enter password when prompted (must be 8+ chars, uppercase, lowercase, digit)

# List users
venv_portal/bin/python usermgr.py list

# You should see your testadmin user listed
```

### 2. Test Admin Server Startup

```bash
# Start admin server
venv_portal/bin/python seenslide_admin.py

# Expected output:
# - If first time: Prompts for admin password setup
# - Then: Shows admin server starting on port 8081
# - Shows API docs at /docs
```

**Test from browser:**
- Open http://localhost:8081
- Should see login page
- Login with your credentials
- Should see dashboard with 3 status cards

### 3. Test Viewer Server Control

From admin dashboard:

**Method 1: Manual viewer start**
1. Click "Start Viewer" button
2. Wait 2-3 seconds
3. Viewer Status card should show "Running" (green)
4. QR code should appear
5. Open http://localhost:8080 in another tab - should see viewer

**Method 2: Auto-start with capture**
1. Fill in session details (name required)
2. Click "Start Capture"
3. Both capture AND viewer should start automatically

### 4. Test Capture Session

**Prerequisites:**
- On Wayland: Must have `dev/config_wayland.yaml` with valid restore_token
- Restore token obtained from first manual capture (grants permission)

**Start Capture:**
1. In admin dashboard
2. Enter Session Name: "Test Session"
3. Select Monitor: 1
4. Click "Start Capture"
5. Watch Capture Status card - should turn green "Active"
6. Should show frame and slide counts updating

**Verify Capture Working:**
```bash
# Check capture is running
ps aux | grep portal | grep -v grep

# Should see a python process running the capture

# Check slides being saved
ls -la /tmp/seenslide/images/

# Should see a directory with UUID (session ID)
# Inside should see .png files being created
```

**Stop Capture:**
1. Click "Stop Capture" button
2. Confirm when prompted
3. Capture Status should turn red "Inactive"
4. Viewer Status should REMAIN green "Running"

### 5. Test Viewer (Desktop)

**Access:**
- Open http://localhost:8080
- Or http://YOUR_IP:8080

**Test Features:**
1. **Session Selection**: Dropdown should list your test session
2. **Select session**: Thumbnails should load on right
3. **Navigation**:
   - Click Previous/Next buttons
   - Use keyboard: ← → arrows
   - Click on thumbnails
   - Use slide number input
4. **Live Mode**:
   - Click LIVE button (should turn green)
   - Start a new capture
   - New slides should auto-display
5. **Fullscreen**:
   - Click fullscreen button or press `F`
   - Should go fullscreen
   - Move mouse - overlay controls appear
   - Wait 3 seconds - controls fade out
   - Press Escape to exit

### 6. Test Viewer (Mobile/Smartphone)

**From your phone on same WiFi:**

1. **Access via QR Code**:
   - Open admin panel on PC: http://YOUR_IP:8081
   - Open camera app on phone
   - Point at QR code
   - Should open viewer automatically

2. **Or access via URL**:
   - Open browser on phone
   - Go to http://YOUR_IP:8080
   - Should see mobile-optimized layout

3. **Test Mobile Features**:
   - Session dropdown should be full-width
   - Thumbnails should scroll horizontally
   - Navigation buttons should be large (44px minimum)
   - Touch/tap should work smoothly
   - Pinch-to-zoom should work on images
   - Landscape mode should adjust layout

4. **Test Fullscreen on Mobile**:
   - Tap fullscreen button
   - Should go fullscreen
   - Touch screen to show controls
   - Controls should be larger (50px)
   - Swipe left/right to navigate

### 7. Test Session Management

**Delete Session:**
1. Stop any active capture first
2. In Sessions Panel, find a test session
3. Click "Delete" button
4. Confirm deletion
5. Session should disappear from list

**Verify Files Deleted:**
```bash
# Check images directory
ls /tmp/seenslide/images/

# The deleted session's directory should be gone
```

## Common Issues & Solutions

### Issue 1: "Screen capture failing when started from admin panel"

**Symptoms:**
- Click "Start Capture" in admin panel
- Capture Status stays "Inactive" or shows error
- No frames being captured

**Solutions:**

1. **Check configuration file exists:**
```bash
ls -la dev/config_wayland.yaml
```

2. **Verify restore token:**
```bash
cat dev/config_wayland.yaml
```
Should have a `restore_token` field with a UUID value.

3. **Get new restore token:**
```bash
# Start capture manually first time
venv_portal/bin/python seenslide.py start "Initial Test" --monitor 1

# This will:
# - Show system permission dialog
# - Generate restore token
# - Save to config file
```

4. **Check portal provider is working:**
```bash
venv_portal/bin/python -c "
from modules.capture.providers.portal_provider import PortalProvider
provider = PortalProvider()
config = {'framerate': 10, 'cursor_mode': 'hidden'}
result = provider.initialize(config)
print(f'Portal provider initialized: {result}')
"
```

5. **Check logs:**
```bash
tail -f /tmp/server.log
```
Look for error messages when starting capture.

### Issue 2: "Viewer not accessible from mobile"

**Symptoms:**
- Can access from PC but not phone
- Connection timeout on mobile
- QR code doesn't work

**Solutions:**

1. **Verify same network:**
   - PC and phone must be on same WiFi
   - Check PC IP: `hostname -I`
   - Try pinging from phone (if possible)

2. **Check firewall:**
```bash
# On Ubuntu, allow ports
sudo ufw allow 8080/tcp
sudo ufw allow 8081/tcp
sudo ufw status
```

3. **Verify viewer is running:**
```bash
# Check if viewer server is listening
netstat -tuln | grep 8080

# Should show something like:
# tcp  0  0.0.0.0:8080  0.0.0.0:*  LISTEN
```

4. **Test direct access:**
   - From mobile browser: http://192.168.1.XXX:8080
   - Replace XXX with your PC's IP address

### Issue 3: "Mobile layout not responsive"

**Symptoms:**
- Text too small on phone
- Buttons too small to tap
- Horizontal scrolling required

**Solutions:**

1. **Clear browser cache:**
   - Mobile browser settings
   - Clear cache and reload
   - Or use incognito/private mode

2. **Force refresh:**
   - On mobile: Pull down to refresh
   - Or: Close browser completely and reopen

3. **Verify CSS loaded:**
   - In browser, view source
   - Check if `<link rel="stylesheet" href="/static/style.css">` is present
   - Access http://YOUR_IP:8080/static/style.css directly
   - Should show CSS content

### Issue 4: "Login fails in admin panel"

**Symptoms:**
- "Invalid username or password" error
- Correct credentials don't work

**Solutions:**

1. **Verify user exists:**
```bash
venv_portal/bin/python usermgr.py list
```

2. **Reset password:**
```bash
venv_portal/bin/python usermgr.py passwd YOUR_USERNAME
```

3. **Check user is active:**
```bash
venv_portal/bin/python usermgr.py list
```
Look for "Active: Yes" column

4. **Activate user if needed:**
```bash
venv_portal/bin/python usermgr.py activate YOUR_USERNAME
```

### Issue 5: "Fullscreen not working"

**Symptoms:**
- Clicking fullscreen button does nothing
- F key doesn't work
- On iOS: fullscreen not available

**Solutions:**

1. **Browser compatibility:**
   - Works on: Chrome, Firefox, Edge, Safari (desktop)
   - Limited on: iOS Safari (no true fullscreen API)
   - Try different browser if issues persist

2. **Keyboard shortcut:**
   - Press `F` key (capital or lowercase)
   - Or use fullscreen button

3. **Check JavaScript console:**
   - Press F12 → Console tab
   - Look for errors when clicking fullscreen

4. **iOS workaround:**
   - Use "Add to Home Screen"
   - Open from home screen (web app mode)
   - Provides more immersive experience

### Issue 6: "QR code not showing"

**Symptoms:**
- QR code area is blank in admin panel
- "QR code library not installed" error

**Solutions:**

1. **Install QR code library:**
```bash
venv_portal/bin/pip install qrcode[pil]
```

2. **Verify installation:**
```bash
venv_portal/bin/python -c "import qrcode; print('QR code installed')"
```

3. **Restart admin server:**
   - Stop server (Ctrl+C)
   - Start again: `venv_portal/bin/python seenslide_admin.py`

## Performance Testing

### Test Capture Performance

```bash
# Start a capture session
# Let it run for 1 minute
# Check statistics

# Count captured images
find /tmp/seenslide/images/ -name "*.png" | wc -l

# Check capture rate
# Should be close to configured FPS (default 10 FPS)
# 1 minute = 600 frames at 10 FPS
```

### Test Mobile Performance

1. **Network speed test:**
   - Open viewer on mobile
   - Switch between slides rapidly
   - Should load within 1-2 seconds

2. **Battery impact:**
   - Monitor battery drain while viewing
   - Live mode may use more battery (WebSocket)

3. **Data usage:**
   - Check mobile data if not on WiFi
   - Each slide ~100-500KB depending on content

## Debug Mode

### Enable Verbose Logging

```bash
# Start admin server with debug logging
venv_portal/bin/python seenslide_admin.py --verbose

# Or edit the server code temporarily:
# In seenslide/app_starter.py:
# logging.basicConfig(level=logging.DEBUG, ...)
```

### Check Database

```bash
# View sessions in database
venv_portal/bin/python -c "
from modules.storage.providers.sqlite_provider import SQLiteStorageProvider

db = SQLiteStorageProvider()
db.initialize({'base_path': '/tmp/seenslide'})

sessions = db.get_all_sessions()
for s in sessions:
    print(f'Session: {s.name} | ID: {s.session_id} | Slides: {s.total_slides}')
"
```

### API Testing

```bash
# Test admin API endpoints (requires authentication cookie)
# First login to get cookie, then:

# Get sessions
curl http://localhost:8081/api/sessions

# Start viewer
curl -X POST http://localhost:8081/api/viewer/start

# Get status
curl http://localhost:8081/api/sessions/status

# Get viewer status
curl http://localhost:8081/api/viewer/status
```

## Production Deployment Checklist

Before using in production presentation:

- [ ] Test complete workflow end-to-end
- [ ] Verify mobile access from test phone
- [ ] Test fullscreen mode works
- [ ] Verify capture starts/stops correctly
- [ ] Test with actual presentation content
- [ ] Ensure WiFi network is stable
- [ ] Have backup plan (manual slide sharing)
- [ ] Test QR code scanning works
- [ ] Verify storage has enough space
- [ ] Test with expected audience size (concurrent viewers)

## Getting Help

If issues persist:

1. Check logs: `/tmp/server.log`
2. Review admin guide: `ADMIN_GUIDE.md`
3. Check GitHub issues
4. Enable debug logging for more details
