#!/usr/bin/env python3
"""Comprehensive test suite for EdgeADC Octavia Driver."""
import sys
import time
sys.path.insert(0, '/software/octavia-edgeadc-driver')

from octavia_edgeadc_driver.api.edgeadc_client import EdgeADCClient

HOST = "192.168.3.159"
USER = "admin"
PASS = "1nSpa1n1234"

# Test data
TEST_VIPS = [
    {"ip": "192.168.3.240", "port": 80, "protocol": "HTTP", "name": "test-http"},
    {"ip": "192.168.3.241", "port": 443, "protocol": "HTTPS", "name": "test-https"},
    {"ip": "192.168.3.242", "port": 3306, "protocol": "TCP", "name": "test-tcp"},
]

TEST_MEMBERS = [
    {"ip": "10.0.0.10", "port": 8080, "weight": 100},
    {"ip": "10.0.0.11", "port": 8080, "weight": 50},
    {"ip": "10.0.0.12", "port": 8080, "weight": 25},
]

results = {"passed": 0, "failed": 0, "tests": []}

def test(name, condition, details=""):
    status = "PASS" if condition else "FAIL"
    results["passed" if condition else "failed"] += 1
    results["tests"].append({"name": name, "status": status, "details": details})
    print(f"  [{status}] {name}" + (f" - {details}" if details and not condition else ""))
    return condition

print("=" * 60)
print("COMPREHENSIVE EDGEADC DRIVER TEST SUITE")
print("=" * 60)
print(f"Target: {HOST}")
print()

client = EdgeADCClient(HOST, USER, PASS)

# ============ AUTHENTICATION TESTS ============
print("\n--- AUTHENTICATION TESTS ---")
guid = client.login()
test("Login returns GUID", guid is not None)
test("GUID is valid format", guid and len(guid) == 32)

# Test re-login
guid2 = client.login()
test("Re-login works", guid2 is not None)

# ============ SYSTEM INFO TESTS ============
print("\n--- SYSTEM INFO TESTS ---")
sys_info = client.get_system_info()
test("Get system info", isinstance(sys_info, dict))
test("System info has data", "data" in sys_info or len(sys_info) > 0)

# ============ VIP LISTING TESTS ============
print("\n--- VIP LISTING TESTS ---")
initial_vips = client.get_ip_services()
test("Get IP services returns list", isinstance(initial_vips, list))
test("Existing VIPs found", len(initial_vips) > 0, f"Found {len(initial_vips)} VIPs")

# ============ VIP CREATION TESTS ============
print("\n--- VIP CREATION TESTS ---")
created_vips = []

for vip_data in TEST_VIPS:
    print(f"\n  Creating {vip_data['protocol']} VIP: {vip_data['ip']}:{vip_data['port']}")
    success, result = client.create_virtual_service(
        ip_addr=vip_data["ip"],
        port=vip_data["port"],
        protocol=vip_data["protocol"],
        service_name=vip_data["name"]
    )
    test(f"Create {vip_data['protocol']} VIP", success)
    
    if success:
        # Verify it exists
        time.sleep(0.3)
        vips = client.get_ip_services()
        found = any(v.get("ipAddr") == vip_data["ip"] and str(v.get("port")) == str(vip_data["port"]) for v in vips)
        test(f"Verify {vip_data['protocol']} VIP exists", found)
        if found:
            created_vips.append(vip_data)

# ============ MEMBER TESTS ============
print("\n--- MEMBER TESTS ---")

if created_vips:
    test_vip = created_vips[0]
    print(f"\n  Using VIP: {test_vip['ip']}:{test_vip['port']}")
    
    # Add members
    added_members = []
    for member in TEST_MEMBERS:
        print(f"\n  Adding member: {member['ip']}:{member['port']} (weight={member['weight']})")
        success, result = client.add_member(
            vip_ip=test_vip["ip"],
            vip_port=test_vip["port"],
            member_ip=member["ip"],
            member_port=member["port"],
            weight=member["weight"]
        )
        test(f"Add member {member['ip']}", success)
        if success:
            added_members.append(member)
    
    # Get members
    time.sleep(0.3)
    members = client.get_members(test_vip["ip"], test_vip["port"])
    test("Get members returns list", isinstance(members, list))
    test("All members added", len(members) >= len(added_members), f"Found {len(members)} members")
    
    # Check member details
    for member in added_members:
        found = any(m.get("ip_address") == member["ip"] and m.get("port") == member["port"] for m in members)
        test(f"Member {member['ip']} found in list", found)
    
    # Update member weight
    if added_members:
        target_member = added_members[0]
        new_weight = 75
        print(f"\n  Updating weight for {target_member['ip']} to {new_weight}")
        success = client.update_member_weight(
            vip_ip=test_vip["ip"],
            vip_port=test_vip["port"],
            member_ip=target_member["ip"],
            member_port=target_member["port"],
            weight=new_weight
        )
        test("Update member weight", success)
        
        # Verify weight changed
        time.sleep(0.3)
        members = client.get_members(test_vip["ip"], test_vip["port"])
        for m in members:
            if m.get("ip_address") == target_member["ip"]:
                test("Weight updated correctly", m.get("weight") == new_weight, f"Weight is {m.get('weight')}")
                break
    
    # Delete members
    print("\n  Deleting members...")
    for member in added_members:
        success = client.delete_member(
            vip_ip=test_vip["ip"],
            vip_port=test_vip["port"],
            member_ip=member["ip"],
            member_port=member["port"]
        )
        test(f"Delete member {member['ip']}", success)
    
    # Verify members deleted
    time.sleep(0.3)
    members = client.get_members(test_vip["ip"], test_vip["port"])
    test("All members deleted", len(members) == 0, f"Remaining: {len(members)}")

else:
    print("  SKIPPED - No VIPs were created")

# ============ VIP DELETION TESTS ============
print("\n--- VIP DELETION TESTS ---")

for vip_data in created_vips:
    print(f"\n  Deleting VIP: {vip_data['ip']}:{vip_data['port']}")
    success = client.delete_virtual_service(vip_data["ip"], vip_data["port"])
    test(f"Delete {vip_data['protocol']} VIP", success)

# Verify all test VIPs deleted
time.sleep(0.5)
final_vips = client.get_ip_services()
remaining_test_vips = [v for v in final_vips if v.get("ipAddr", "").startswith("192.168.3.24")]
test("All test VIPs cleaned up", len(remaining_test_vips) == 0, f"Remaining: {len(remaining_test_vips)}")

# ============ ERROR HANDLING TESTS ============
print("\n--- ERROR HANDLING TESTS ---")

# Try to delete non-existent VIP
success = client.delete_virtual_service("1.2.3.4", 9999)
test("Delete non-existent VIP returns False", not success)

# Try to add member to non-existent VIP
success, _ = client.add_member("1.2.3.4", 9999, "10.0.0.1", 80, 100)
test("Add member to non-existent VIP returns False", not success)

# Try to get members for non-existent VIP
members = client.get_members("1.2.3.4", 9999)
test("Get members for non-existent VIP returns empty", len(members) == 0)

# ============ APPLY CONFIG TEST ============
print("\n--- APPLY CONFIG TEST ---")
success = client.apply_config()
test("Apply config", success)

# ============ CLEANUP VERIFICATION ============
print("\n--- CLEANUP VERIFICATION ---")
final_vips = client.get_ip_services()
original_count = len(initial_vips)
final_count = len([v for v in final_vips if v.get("ipAddr")])  # Count non-empty VIPs
test("VIP count restored", final_count == original_count, f"Before: {original_count}, After: {final_count}")

client.close()

# ============ SUMMARY ============
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print(f"Total Tests: {results['passed'] + results['failed']}")
print(f"Passed: {results['passed']}")
print(f"Failed: {results['failed']}")
print(f"Success Rate: {results['passed'] / (results['passed'] + results['failed']) * 100:.1f}%")

if results['failed'] > 0:
    print("\nFailed Tests:")
    for t in results['tests']:
        if t['status'] == 'FAIL':
            print(f"  - {t['name']}: {t['details']}")

print("\n" + "=" * 60)
if results['failed'] == 0:
    print("ALL TESTS PASSED! ✓")
else:
    print(f"SOME TESTS FAILED ({results['failed']})")
print("=" * 60)
