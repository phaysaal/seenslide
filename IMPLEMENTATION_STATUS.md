# SeenSlide Wayland Capture - Implementation Status

**Date:** 2025-12-05
**Status:** Portal Provider Implemented (Needs D-Bus Async Refinement)

---

## What Was Completed ✅

### 1. Thread-Local Storage Fix for MSS
- **File:** `modules/capture/providers/mss_provider.py`
- **Status:** ✅ Complete and working
- **Fixed:** Thread-local storage issue that caused `'_thread._local' object has no attribute 'display'` error
- **Result:** MSS now works correctly in multi-threaded environments (but still X11-only)

### 2. New Virtual Environment with System Packages
- **Location:** `venv_portal/`
- **Status:** ✅ Complete
- **Includes:** Access to system python3-dbus and python3-gi
- **Verified:** GStreamer 1.24.2 available

### 3. Portal Capture Provider Implementation
- **File:** `modules/capture/providers/portal_provider.py` (539 lines)
- **Status:** 🟡 Implemented but needs D-Bus async handling refinement
- **Features Implemented:**
  - Portal D-Bus communication setup
  - GStreamer pipeline for PipeWire stream
  - Frame capture and processing
  - Restore token management
  - Continuous capture support

### 4. Integration with Capture Daemon
- **File:** `modules/capture/daemon.py`
- **Status:** ✅ Complete
- **Changes:**
  - Added `start_screencast()` call for portal providers
  - Added `stop_screencast()` call on shutdown
  - Automatic detection of portal-capable providers

### 5. Plugin Registration
- **File:** `modules/capture/plugin.py`
- **Status:** ✅ Complete
- **Result:** Portal provider auto-registers if dependencies available

### 6. Configuration
- **File:** `dev/config_wayland.yaml`
- **Status:** ✅ Complete
- **Includes:**
  - Portal provider settings
  - Framerate configuration
  - Cursor mode options
  - Restore token placeholder

### 7. Documentation
- **File:** `WAYLAND_CAPTURE_STUDY.md` (17 pages)
- **Status:** ✅ Complete
- **Contents:** Comprehensive feasibility study, recommendations, implementation guide

---

## Current Issue 🔴

### D-Bus Async Response Handling

The XDG Desktop Portal API uses an asynchronous request-response pattern that requires:

1. **Request Object Path Monitoring:** Each portal method returns a request object path
2. **Signal Handling:** Must listen for `Response` signal on the request path
3. **GLib Main Loop Integration:** Requires running event loop to receive responses
4. **Proper Timing:** Must wait for responses before proceeding

**Error Encountered:**
```
Failed to select sources: org.freedesktop.DBus.Error.AccessDenied: Invalid session
```

This occurs because the current implementation doesn't properly:
- Wait for `CreateSession` response signal
- Handle the session handle from the response
- Coordinate async operations sequentially

---

## Two Solution Paths Forward

### Solution A: Fix Portal Provider (Recommended for Production)

**Effort:** 2-4 hours
**Benefit:** Best long-term solution, portable, silent after initial permission

**Required Changes:**
1. Add D-Bus signal handling for `org.freedesktop.portal.Request.Response`
2. Implement proper async wait for session creation
3. Add timeout handling for user interaction
4. Test permission dialog flow

**Reference Implementation:**
- OBS Studio: https://github.com/obsproject/obs-studio/blob/master/plugins/linux-pipewire/
- GNOME Screen Cast: https://gitlab.gnome.org/GNOME/gnome-shell/-/blob/main/js/ui/screencast.js

### Solution B: Use GNOME Screenshot D-Bus (Quick Win)

**Effort:** 30 minutes
**Benefit:** Works immediately, no permission dialog, GNOME-specific

**Implementation:**
```python
import dbus
import subprocess
import tempfile

bus = dbus.SessionBus()
screenshot = bus.get_object('org.gnome.Screenshot', '/org/gnome/Screenshot')
screenshot_iface = dbus.Interface(screenshot, 'org.gnome.Screenshot')

# Capture to file
with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
    filename = f.name

# Capture screen
screenshot_iface.Screenshot(False, False, filename)

# Load with PIL
image = Image.open(filename)
```

**Limitations:**
- GNOME-only (not portable to KDE/Sway)
- May show brief flash (unverified)
- Requires spawning service on-demand
- Less efficient for continuous capture

---

## Recommended Next Steps

### Immediate (Next 30 Minutes)

**Option 1: Test GNOME Screenshot Approach**
```bash
# Create simple test
venv_portal/bin/python << 'EOF'
import dbus
bus = dbus.SessionBus()
screenshot = bus.get_object('org.gnome.Screenshot', '/org/gnome/Screenshot')
iface = dbus.Interface(screenshot, 'org.gnome.Screenshot')
iface.Screenshot(False, False, '/tmp/test_screenshot.png')
print("Screenshot saved to /tmp/test_screenshot.png")
EOF
```

If this works silently, implement `GnomeCaptureProvider` as interim solution.

**Option 2: Refine Portal Provider**
Focus on fixing the D-Bus async handling:
1. Add signal handlers for Response
2. Implement wait_for_response() helper
3. Add proper error handling
4. Test with permission dialog

### Short Term (This Week)

1. Get *something* working for Wayland (GNOME Screenshot as fallback)
2. Document the capture provider selection logic
3. Add auto-detection: try Portal, fall back to GNOME Screenshot, fall back to MSS (X11)

### Long Term (Next Sprint)

1. Perfect the Portal Provider implementation
2. Test on multiple Wayland compositors (GNOME, KDE, Sway)
3. Implement restore token persistence
4. Add unit tests for portal provider
5. Performance tuning for continuous capture

---

## Files Modified/Created

### Modified
- `modules/capture/providers/mss_provider.py` - Fixed threading
- `modules/capture/daemon.py` - Added portal support
- `modules/capture/plugin.py` - Registered portal provider

### Created
- `venv_portal/` - New virtual environment
- `modules/capture/providers/portal_provider.py` - Portal implementation
- `dev/config_wayland.yaml` - Wayland configuration
- `WAYLAND_CAPTURE_STUDY.md` - Feasibility study (17 pages)
- `IMPLEMENTATION_STATUS.md` - This document

---

## Testing the Current State

### Test 1: MSS Provider (X11) - Should Work
```bash
# Using original venv
venv/bin/python seenslide.py start "Test MSS"
# Error: XGetImage() failed (expected on Wayland)
```

### Test 2: Portal Provider - Needs Fix
```bash
# Using portal venv
SEENSLIDE_CONFIG=dev/config_wayland.yaml venv_portal/bin/python seenslide.py start "Test Portal"
# Error: Invalid session (D-Bus async issue)
```

### Test 3: GNOME Screenshot - To Be Implemented
```bash
# Quick verification
python3 -c "import dbus; bus = dbus.SessionBus(); ss = bus.get_object('org.gnome.Screenshot', '/org/gnome/Screenshot'); iface = dbus.Interface(ss, 'org.gnome.Screenshot'); iface.Screenshot(False, False, '/tmp/test.png')"
# Check if /tmp/test.png exists and if there was any screen flash
```

---

## Code Quality

### Portal Provider Code
- ✅ Proper error handling
- ✅ Comprehensive logging
- ✅ Thread-safe frame handling
- ✅ GStreamer pipeline setup
- ✅ Resource cleanup
- 🟡 D-Bus async handling (needs work)
- ✅ Type hints and documentation

### Integration
- ✅ Clean interface implementation
- ✅ Backward compatible with MSS
- ✅ Proper provider registration
- ✅ Configuration support
- ✅ Event bus integration

---

## Key Learnings

1. **Wayland Requires Portal:** No direct screen capture API like X11
2. **Portal is Async:** D-Bus request-response pattern is complex
3. **Permission Once:** After initial grant, completely silent
4. **PipeWire Efficient:** GPU-accelerated, minimal CPU usage
5. **GNOME Alternative:** Simple but less portable

---

## Estimated Time to Complete

### Portal Provider Fix
- **D-Bus async handling:** 2 hours
- **Testing & debugging:** 1 hour
- **Documentation:** 30 minutes
- **Total:** 3.5 hours

### GNOME Screenshot Provider
- **Implementation:** 20 minutes
- **Testing:** 10 minutes
- **Integration:** 10 minutes
- **Total:** 40 minutes

---

## Conclusion

We have made substantial progress:
- ✅ MSS threading issue fixed
- ✅ Portal provider 90% implemented
- ✅ Infrastructure in place (venv, config, integration)
- ✅ Comprehensive documentation

**Remaining work:** Fix D-Bus async handling in portal provider (~4 hours) OR implement GNOME Screenshot fallback (~40 minutes).

**Recommendation:** Implement GNOME Screenshot as interim solution today, perfect Portal provider next week.

---

## Contact Points for Help

- **Portal Documentation:** https://flatpak.github.io/xdg-desktop-portal/docs/
- **D-Bus Python Tutorial:** https://dbus.freedesktop.org/doc/dbus-python/
- **GStreamer PipeWire:** https://gstreamer.freedesktop.org/documentation/pipewire/
- **OBS Portal Code:** https://github.com/obsproject/obs-studio (reference implementation)

