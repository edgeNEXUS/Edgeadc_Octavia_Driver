#!/usr/bin/env python3
"""Full test suite for EdgeADC Octavia Driver - all possible tests."""
import sys
import time
import json
sys.path.insert(0, '/software/octavia-edgeadc-driver')

from octavia_edgeadc_driver.api.edgeadc_client import EdgeADCClient

HOST = "192.168.3.159"
USER = "admin"
PASS = "1nSpa1n1234"

results = {"passed": 0, "failed": 0, "skipped": 0, "tests": []}

def test(name, condition, details="", skip=False):
    if skip:
        results["skipped"] += 1
        results["tests"].append({"name": name, "status": "SKIP", "details": details})
        print(f"  [SKIP] {name}" + (f" - {details}" if details else ""))
        return None
    status = "PASS" if condition else "FAIL"
    results["passed" if condition else "failed"] += 1
    results["tests"].append({"name": name, "status": status, "details": details})
    print(f"  [{status}] {name}" + (f" - {details}" if details and not condition else ""))
    return condition

print("=" * 70)
print("FULL EDGEADC DRIVER TEST SUITE")
print("=" * 70)
print(f"Target: {HOST}")
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print()

client = EdgeADCClient(HOST, USER, PASS)

# ============ 1. AUTHENTICATION ============
print("\n[1] AUTHENTICATION TESTS")
print("-" * 50)
guid = client.login()
test("1.1 Login returns GUID", guid is not None)
test("1.2 GUID is 32 chars", guid and len(guid) == 32, f"len={len(guid) if guid else 0}")
test("1.3 Re-login works", client.login() is not None)

# ============ 2. SYSTEM INFO ============
print("\n[2] SYSTEM INFO TESTS")
print("-" * 50)
sys_info = client.get_system_info()
test("2.1 Get system info", isinstance(sys_info, dict))
test("2.2 Response not empty", len(sys_info) > 0)

# ============ 3. IP SERVICES (VIP) LISTING ============
print("\n[3] VIP LISTING TESTS")
print("-" * 50)
initial_vips = client.get_ip_services()
test("3.1 Returns list", isinstance(initial_vips, list))
initial_count = len([v for v in initial_vips if v.get('ipAddr')])
test("3.2 Found existing VIPs", initial_count > 0, f"count={initial_count}")

# Print existing VIPs
print(f"  Existing VIPs:")
for v in initial_vips[:5]:
    if v.get('ipAddr'):
        print(f"    - {v.get('ipAddr')}:{v.get('port')} ({v.get('serviceName')})")

# ============ 4. VIP CREATION - DIFFERENT PROTOCOLS ============
print("\n[4] VIP CREATION TESTS (Multiple Protocols)")
print("-" * 50)

test_vips = [
    {"ip": "192.168.3.230", "port": 80, "protocol": "HTTP", "name": "test-http-80"},
    {"ip": "192.168.3.231", "port": 443, "protocol": "HTTPS", "name": "test-https-443"},
    {"ip": "192.168.3.232", "port": 3306, "protocol": "TCP", "name": "test-tcp-mysql"},
    {"ip": "192.168.3.233", "port": 53, "protocol": "UDP", "name": "test-udp-dns"},
    {"ip": "192.168.3.234", "port": 8080, "protocol": "HTTP", "name": "test-http-alt"},
]

created_vips = []
for vip in test_vips:
    success, result = client.create_virtual_service(
        ip_addr=vip["ip"],
        port=vip["port"],
        protocol=vip["protocol"],
        service_name=vip["name"]
    )
    if test(f"4.{len(created_vips)+1} Create {vip['protocol']} VIP {vip['ip']}:{vip['port']}", success):
        created_vips.append(vip)
    time.sleep(0.2)

# Verify all created
time.sleep(0.5)
vips = client.get_ip_services()
for vip in created_vips:
    found = any(v.get("ipAddr") == vip["ip"] and str(v.get("port")) == str(vip["port"]) for v in vips)
    test(f"4.{len(created_vips)+1+created_vips.index(vip)} Verify {vip['name']} exists", found)

# ============ 5. MEMBER OPERATIONS ============
print("\n[5] MEMBER OPERATIONS TESTS")
print("-" * 50)

if created_vips:
    test_vip = created_vips[0]
    print(f"  Using VIP: {test_vip['ip']}:{test_vip['port']}")
    
    test_members = [
        {"ip": "10.0.0.1", "port": 8080, "weight": 100},
        {"ip": "10.0.0.2", "port": 8080, "weight": 80},
        {"ip": "10.0.0.3", "port": 8080, "weight": 60},
        {"ip": "10.0.0.4", "port": 8080, "weight": 40},
        {"ip": "10.0.0.5", "port": 8080, "weight": 20},
    ]
    
    added = []
    for i, m in enumerate(test_members):
        success, _ = client.add_member(test_vip["ip"], test_vip["port"], m["ip"], m["port"], m["weight"])
        if test(f"5.{i+1} Add member {m['ip']}:{m['port']}", success):
            added.append(m)
        time.sleep(0.2)
    
    # Get members
    time.sleep(0.3)
    members = client.get_members(test_vip["ip"], test_vip["port"])
    test(f"5.{len(test_members)+1} Get members returns list", isinstance(members, list))
    test(f"5.{len(test_members)+2} All members present", len(members) >= len(added), f"got {len(members)}")
    
    # Verify each member
    for m in added:
        found = any(mem.get("ip_address") == m["ip"] and mem.get("port") == m["port"] for mem in members)
        test(f"5.{len(test_members)+3+added.index(m)} Member {m['ip']} in list", found)
    
    # Delete members
    for i, m in enumerate(added):
        success = client.delete_member(test_vip["ip"], test_vip["port"], m["ip"], m["port"])
        test(f"5.{len(test_members)*2+4+i} Delete member {m['ip']}", success)
        time.sleep(0.1)
    
    # Verify all deleted
    time.sleep(0.3)
    members = client.get_members(test_vip["ip"], test_vip["port"])
    test(f"5.{len(test_members)*3+4} All members deleted", len(members) == 0, f"remaining={len(members)}")
else:
    test("5.x Member tests", False, "No VIPs created", skip=True)

# ============ 6. SAME IP DIFFERENT PORTS ============
print("\n[6] SAME IP DIFFERENT PORTS TESTS")
print("-" * 50)

same_ip = "192.168.3.235"
ports = [80, 443, 8080, 8443]
same_ip_vips = []

for port in ports:
    success, _ = client.create_virtual_service(same_ip, port, "HTTP", "255.255.255.0", f"multi-{port}")
    if test(f"6.{ports.index(port)+1} Create {same_ip}:{port}", success):
        same_ip_vips.append({"ip": same_ip, "port": port})
    time.sleep(0.2)

# Verify
time.sleep(0.3)
vips = client.get_ip_services()
for v in same_ip_vips:
    found = any(x.get("ipAddr") == v["ip"] and str(x.get("port")) == str(v["port"]) for x in vips)
    test(f"6.{len(ports)+1+same_ip_vips.index(v)} Verify {v['ip']}:{v['port']}", found)

# ============ 7. VIP DELETION ============
print("\n[7] VIP DELETION TESTS")
print("-" * 50)

# Delete all created VIPs
all_test_vips = created_vips + same_ip_vips
for i, vip in enumerate(all_test_vips):
    success = client.delete_virtual_service(vip["ip"], vip["port"])
    test(f"7.{i+1} Delete {vip['ip']}:{vip['port']}", success)
    time.sleep(0.1)

# Verify all deleted
time.sleep(0.5)
vips = client.get_ip_services()
remaining = [v for v in vips if v.get("ipAddr", "").startswith("192.168.3.23")]
test(f"7.{len(all_test_vips)+1} All test VIPs deleted", len(remaining) == 0, f"remaining={len(remaining)}")

# ============ 8. ERROR HANDLING ============
print("\n[8] ERROR HANDLING TESTS")
print("-" * 50)

# Non-existent VIP operations
test("8.1 Delete non-existent VIP", not client.delete_virtual_service("1.2.3.4", 9999))
success, _ = client.add_member("1.2.3.4", 9999, "10.0.0.1", 80, 100)
test("8.2 Add member to non-existent VIP", not success)
test("8.3 Get members non-existent VIP", len(client.get_members("1.2.3.4", 9999)) == 0)
test("8.4 Delete non-existent member", not client.delete_member("1.2.3.4", 9999, "10.0.0.1", 80))

# ============ 9. APPLY CONFIG ============
print("\n[9] CONFIG APPLICATION TESTS")
print("-" * 50)
test("9.1 Apply config", client.apply_config())

# ============ 10. FINAL VERIFICATION ============
print("\n[10] FINAL VERIFICATION")
print("-" * 50)
final_vips = client.get_ip_services()
final_count = len([v for v in final_vips if v.get('ipAddr')])
test("10.1 VIP count restored", final_count == initial_count, f"before={initial_count}, after={final_count}")

client.close()

# ============ SUMMARY ============
print("\n" + "=" * 70)
print("TEST RESULTS SUMMARY")
print("=" * 70)
total = results['passed'] + results['failed']
print(f"Total Tests:  {total}")
print(f"Passed:       {results['passed']} ({results['passed']/total*100:.1f}%)" if total > 0 else "")
print(f"Failed:       {results['failed']}")
print(f"Skipped:      {results['skipped']}")

if results['failed'] > 0:
    print("\nFAILED TESTS:")
    for t in results['tests']:
        if t['status'] == 'FAIL':
            print(f"  ✗ {t['name']}: {t['details']}")

print("\n" + "=" * 70)
if results['failed'] == 0:
    print("✓ ALL TESTS PASSED!")
    confidence = 95.0
else:
    confidence = results['passed'] / total * 100 if total > 0 else 0
    print(f"✗ {results['failed']} TEST(S) FAILED")

print(f"\nCONFIDENCE LEVEL: {confidence:.1f}%")
print("=" * 70)
