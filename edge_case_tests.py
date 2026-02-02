#!/usr/bin/env python3
"""Edge case and stress tests for EdgeADC driver."""
import sys
import time
sys.path.insert(0, '/software/octavia-edgeadc-driver')

from octavia_edgeadc_driver.api.edgeadc_client import EdgeADCClient

HOST = "192.168.3.159"
USER = "admin"
PASS = "1nSpa1n1234"

results = {"passed": 0, "failed": 0}

def test(name, condition, details=""):
    status = "PASS" if condition else "FAIL"
    results["passed" if condition else "failed"] += 1
    print(f"  [{status}] {name}" + (f" - {details}" if details and not condition else ""))
    return condition

print("=" * 60)
print("EDGE CASE & STRESS TESTS")
print("=" * 60)

client = EdgeADCClient(HOST, USER, PASS)
client.login()

# ============ 1. SPECIAL PORT NUMBERS ============
print("\n[1] SPECIAL PORT NUMBERS")
print("-" * 50)

special_ports = [
    (1, "Port 1 (lowest)"),
    (22, "Port 22 (SSH)"),
    (443, "Port 443 (HTTPS)"),
    (8080, "Port 8080 (Alt HTTP)"),
    (32767, "Port 32767 (high)"),
    (65535, "Port 65535 (max)"),
]

created = []
for port, desc in special_ports:
    ip = "192.168.3.220"
    success, _ = client.create_virtual_service(ip, port, "TCP", "255.255.255.0", f"test-{port}")
    if test(f"1.{len(created)+1} Create {desc}", success):
        created.append((ip, port))
    time.sleep(0.3)

# Cleanup
for ip, port in created:
    client.delete_virtual_service(ip, port)
time.sleep(0.3)

# ============ 2. RAPID VIP CREATE/DELETE ============
print("\n[2] RAPID VIP CREATE/DELETE (10 cycles)")
print("-" * 50)

rapid_success = 0
for i in range(10):
    ip = "192.168.3.221"
    port = 9000 + i
    success1, _ = client.create_virtual_service(ip, port, "HTTP", "255.255.255.0", f"rapid-{i}")
    success2 = client.delete_virtual_service(ip, port)
    if success1 and success2:
        rapid_success += 1
    time.sleep(0.2)

test("2.1 Rapid create/delete cycles", rapid_success == 10, f"{rapid_success}/10 succeeded")

# ============ 3. MANY MEMBERS ON SINGLE VIP ============
print("\n[3] MANY MEMBERS ON SINGLE VIP (20 members)")
print("-" * 50)

ip, port = "192.168.3.222", 8080
client.create_virtual_service(ip, port, "HTTP", "255.255.255.0", "many-members")
time.sleep(0.5)

member_count = 0
for i in range(20):
    success, _ = client.add_member(ip, port, f"10.1.1.{i+1}", 8080, 100)
    if success:
        member_count += 1
    time.sleep(0.1)

test("3.1 Add 20 members", member_count == 20, f"{member_count}/20 added")

# Get members
members = client.get_members(ip, port)
test("3.2 Retrieve all members", len(members) == 20, f"got {len(members)}")

# Delete all members
deleted = 0
for i in range(20):
    if client.delete_member(ip, port, f"10.1.1.{i+1}", 8080):
        deleted += 1

test("3.3 Delete all members", deleted == 20, f"{deleted}/20 deleted")

# Cleanup
client.delete_virtual_service(ip, port)

# ============ 4. DUPLICATE VIP HANDLING ============
print("\n[4] DUPLICATE VIP HANDLING")
print("-" * 50)

ip, port = "192.168.3.223", 8888
success1, _ = client.create_virtual_service(ip, port, "HTTP", "255.255.255.0", "dup-test-1")
time.sleep(0.3)
success2, _ = client.create_virtual_service(ip, port, "HTTP", "255.255.255.0", "dup-test-2")

test("4.1 First VIP created", success1)
# Second should succeed but create a new entry (or fail gracefully)
print(f"  [INFO] Second VIP create returned: {success2}")

# Cleanup
client.delete_virtual_service(ip, port)
time.sleep(0.3)

# ============ 5. DUPLICATE MEMBER HANDLING ============
print("\n[5] DUPLICATE MEMBER HANDLING")
print("-" * 50)

ip, port = "192.168.3.224", 7777
client.create_virtual_service(ip, port, "HTTP", "255.255.255.0", "dup-member")
time.sleep(0.3)

success1, _ = client.add_member(ip, port, "10.2.2.1", 8080, 100)
time.sleep(0.2)
success2, _ = client.add_member(ip, port, "10.2.2.1", 8080, 100)  # Same member again

test("5.1 First member added", success1)
print(f"  [INFO] Duplicate member add returned: {success2}")

members = client.get_members(ip, port)
print(f"  [INFO] Total members after duplicate add: {len(members)}")

# Cleanup
client.delete_member(ip, port, "10.2.2.1", 8080)
client.delete_virtual_service(ip, port)

# ============ 6. DIFFERENT SUBNET MASKS ============
print("\n[6] DIFFERENT SUBNET MASKS")
print("-" * 50)

masks = [
    ("255.255.255.0", "/24"),
    ("255.255.0.0", "/16"),
    ("255.255.255.128", "/25"),
    ("255.255.255.252", "/30"),
]

mask_results = []
for i, (mask, desc) in enumerate(masks):
    ip = f"192.168.3.{225+i}"
    success, _ = client.create_virtual_service(ip, 8080, "HTTP", mask, f"mask-{desc}")
    if test(f"6.{i+1} Create VIP with {desc} mask", success):
        mask_results.append((ip, 8080))
    time.sleep(0.3)

# Cleanup
for ip, port in mask_results:
    client.delete_virtual_service(ip, port)

# ============ 7. SESSION PERSISTENCE ============
print("\n[7] SESSION PERSISTENCE")
print("-" * 50)

# Create new client instance
client2 = EdgeADCClient(HOST, USER, PASS)
guid2 = client2.login()
test("7.1 Second client login", guid2 is not None)

# Both clients can list VIPs
vips1 = client.get_ip_services()
vips2 = client2.get_ip_services()
test("7.2 Both clients see same VIPs", len(vips1) == len(vips2))

client2.close()

# ============ 8. LONG SERVICE NAMES ============
print("\n[8] LONG SERVICE NAMES")
print("-" * 50)

long_name = "a" * 100  # 100 character name
ip, port = "192.168.3.229", 9999
success, _ = client.create_virtual_service(ip, port, "HTTP", "255.255.255.0", long_name)
test("8.1 Create VIP with 100 char name", success)

if success:
    vips = client.get_ip_services()
    found = [v for v in vips if v.get("ipAddr") == ip and str(v.get("port")) == str(port)]
    if found:
        actual_name = found[0].get("serviceName", "")
        test("8.2 Name stored (may be truncated)", len(actual_name) > 0, f"got {len(actual_name)} chars")
    client.delete_virtual_service(ip, port)

client.close()

# ============ SUMMARY ============
print("\n" + "=" * 60)
print("EDGE CASE TEST RESULTS")
print("=" * 60)
total = results['passed'] + results['failed']
print(f"Passed: {results['passed']}/{total}")
print(f"Failed: {results['failed']}")

if results['failed'] == 0:
    print("\n✓ ALL EDGE CASE TESTS PASSED!")
print("=" * 60)
