
import sys
import os
import json
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.logs.services import _normalize_log_message, _group_logs_by_pattern

def test_normalization():
    print("Testing Log Normalization...")
    cases = [
        ("User 12345 login failed", "User <NUM> login failed"),
        ("Connection timeout to 192.168.1.1", "Connection timeout to <IP>"),
        ("Error at 2023-10-10T12:00:00Z", "Error at <DATE>"),
        ("UUID 123e4567-e89b-12d3-a456-426614174000 found", "UUID <UUID> found"),
        ("Memory address 0x123abc error", "Memory address <HEX> error"),
        ("Mixed: User 123 at 10.0.0.1", "Mixed: User <NUM> at <IP>"),
    ]
    
    for input_msg, expected in cases:
        normalized = _normalize_log_message(input_msg)
        if normalized == expected:
            print(f"PASS: '{input_msg}' -> '{normalized}'")
        else:
            print(f"FAIL: '{input_msg}'\n      Expected: '{expected}'\n      Actual:   '{normalized}'")

def test_grouping():
    print("\nTesting Log Grouping...")
    
    # Mock logs
    logs = [
        # Pattern A: Timeout (Repeated 3 times)
        {"attributes": {"status": "error", "message": "Connection timeout to 192.168.1.1", "service": "api"}},
        {"attributes": {"status": "error", "message": "Connection timeout to 192.168.1.2", "service": "api"}},
        {"attributes": {"status": "error", "message": "Connection timeout to 10.0.0.5", "service": "api"}},
        
        # Pattern B: User Login (Repeated 2 times)
        {"attributes": {"status": "info", "message": "User 101 login success", "service": "auth"}},
        {"attributes": {"status": "info", "message": "User 202 login success", "service": "auth"}},
        
        # Pattern C: Unique Error
        {"attributes": {"status": "critical", "message": "Disk full on /dev/sda1", "service": "system"}},
    ]
    
    groups = _group_logs_by_pattern(logs)
    
    print(f"Total Groups: {len(groups)}")
    for g in groups:
        print(f"[{g['status']}] {g['service']} (Count: {g['count']}) - {g['pattern_message']}")

    # Assertions
    # Expect 3 groups
    if len(groups) != 3:
        print("FAIL: Expected 3 groups")
        return

    # Check Timeout Pattern (Should be first because it's error + high count)
    # The sort order is Error first, then Count.
    # Pattern C (Critical, 1) vs Pattern A (Error, 3). Both are "error-like". Pattern A has higher count.
    # Wait, my logic: is_error = 1 if status in ["ERROR", "CRITICAL"...]
    # So both A and C have is_error=1.
    # Pattern A count=3, Pattern C count=1.
    # So Pattern A should be first.
    
    if groups[0]['count'] == 3 and "timeout" in groups[0]['pattern_message'].lower():
        print("PASS: Timeout pattern grouped correctly and prioritized")
    else:
        print("FAIL: Timeout pattern order or count incorrect")
        
    if groups[2]['count'] == 2 and "login" in groups[2]['pattern_message'].lower():
        print("PASS: Login pattern grouped correctly")
    else:
        print("FAIL: Login pattern incorrect")

if __name__ == "__main__":
    test_normalization()
    test_grouping()
