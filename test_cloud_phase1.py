#!/usr/bin/env python3
"""Test script for Cloud Server Phase 1 - Session Management."""

import requests
import time
import sys


def test_cloud_server(base_url: str = "http://localhost:8000"):
    """Test cloud server session management endpoints.

    Args:
        base_url: Base URL of the cloud server
    """
    print("=" * 60)
    print("SeenSlide Cloud Server - Phase 1 Test")
    print("=" * 60)
    print()

    # Test 1: Health Check
    print("[TEST 1] Health Check")
    try:
        response = requests.get(f"{base_url}/health")
        response.raise_for_status()
        print(f"✓ Server is healthy: {response.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False
    print()

    # Test 2: Create Session
    print("[TEST 2] Create Session")
    try:
        payload = {
            "presenter_name": "Test Presenter",
            "presenter_email": "test@example.com",
            "max_slides": 50
        }
        response = requests.post(
            f"{base_url}/api/cloud/session/create",
            json=payload
        )
        response.raise_for_status()
        session_data = response.json()
        session_id = session_data["session_id"]
        print(f"✓ Session created: {session_id}")
        print(f"  Presenter: {session_data['presenter_name']}")
        print(f"  Max slides: {session_data['max_slides']}")
        print(f"  Status: {session_data['status']}")
    except Exception as e:
        print(f"✗ Session creation failed: {e}")
        return False
    print()

    # Test 3: Get Session Info
    print("[TEST 3] Get Session Info")
    try:
        response = requests.get(f"{base_url}/api/cloud/session/{session_id}")
        response.raise_for_status()
        info = response.json()
        print(f"✓ Session info retrieved")
        print(f"  Session ID: {info['session_id']}")
        print(f"  Total slides: {info['total_slides']}")
        print(f"  Viewer count: {info['viewer_count']}")
    except Exception as e:
        print(f"✗ Get session info failed: {e}")
        return False
    print()

    # Test 4: Validate Session ID Format
    print("[TEST 4] Validate Session ID Format")
    if len(session_id) == 8 and session_id[3] == '-':
        letters, numbers = session_id.split('-')
        if letters.isupper() and letters.isalpha() and numbers.isdigit():
            print(f"✓ Session ID format is valid: {session_id}")
        else:
            print(f"✗ Session ID format invalid: {session_id}")
            return False
    else:
        print(f"✗ Session ID format invalid: {session_id}")
        return False
    print()

    # Test 5: Test Invalid Session ID
    print("[TEST 5] Test Invalid Session ID")
    try:
        response = requests.get(f"{base_url}/api/cloud/session/INVALID123")
        if response.status_code == 400:
            print("✓ Invalid session ID properly rejected")
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Invalid session test failed: {e}")
        return False
    print()

    # Test 6: List Active Sessions
    print("[TEST 6] List Active Sessions")
    try:
        response = requests.get(f"{base_url}/api/cloud/sessions")
        response.raise_for_status()
        sessions = response.json()["sessions"]
        print(f"✓ Found {len(sessions)} active session(s)")
        for s in sessions:
            print(f"  - {s['session_id']}: {s['presenter_name']}")
    except Exception as e:
        print(f"✗ List sessions failed: {e}")
        return False
    print()

    # Test 7: Get Server Stats
    print("[TEST 7] Get Server Stats")
    try:
        response = requests.get(f"{base_url}/api/cloud/stats")
        response.raise_for_status()
        stats = response.json()
        print(f"✓ Server stats retrieved")
        print(f"  Active sessions: {stats['active_sessions']}")
        print(f"  Total slides: {stats['total_slides']}")
        print(f"  Total viewers: {stats['total_viewers']}")
    except Exception as e:
        print(f"✗ Get stats failed: {e}")
        return False
    print()

    # Test 8: End Session
    print("[TEST 8] End Session")
    try:
        response = requests.delete(f"{base_url}/api/cloud/session/{session_id}")
        response.raise_for_status()
        print(f"✓ Session {session_id} ended successfully")
    except Exception as e:
        print(f"✗ End session failed: {e}")
        return False
    print()

    # Test 9: Verify Session Ended
    print("[TEST 9] Verify Session Ended")
    try:
        response = requests.get(f"{base_url}/api/cloud/session/{session_id}")
        if response.status_code == 404:
            print("✓ Session properly removed after ending")
        else:
            print(f"✗ Session still accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Verify ended session failed: {e}")
        return False
    print()

    # Test 10: Create Multiple Sessions
    print("[TEST 10] Create Multiple Sessions (Uniqueness Test)")
    try:
        session_ids = set()
        for i in range(5):
            payload = {
                "presenter_name": f"Presenter {i+1}",
                "max_slides": 50
            }
            response = requests.post(
                f"{base_url}/api/cloud/session/create",
                json=payload
            )
            response.raise_for_status()
            session_ids.add(response.json()["session_id"])

        if len(session_ids) == 5:
            print(f"✓ Created 5 unique sessions: {session_ids}")
        else:
            print(f"✗ Session ID collision detected")
            return False

        # Clean up
        for sid in session_ids:
            requests.delete(f"{base_url}/api/cloud/session/{sid}")
    except Exception as e:
        print(f"✗ Multiple sessions test failed: {e}")
        return False
    print()

    print("=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test SeenSlide Cloud Server")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Cloud server URL (default: http://localhost:8000)"
    )

    args = parser.parse_args()

    success = test_cloud_server(args.url)
    sys.exit(0 if success else 1)
