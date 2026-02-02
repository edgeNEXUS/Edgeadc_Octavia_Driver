#!/usr/bin/env python3
"""Test VIP create/delete using the updated client."""
import sys
sys.path.insert(0, '/software/octavia-edgeadc-driver')

from octavia_edgeadc_driver.api.edgeadc_client import EdgeADCClient

HOST = "192.168.3.159"
USER = "admin"
PASS = "1nSpa1n1234"

print("=== Testing Updated EdgeADC Client ===\n")

client = EdgeADCClient(HOST, USER, PASS)

# Login
guid = client.login()
print(f"1. Login: {'PASS' if guid else 'FAIL'}")

# List existing VIPs
print("\n2. Existing VIPs:")
vips = client.get_ip_services()
for v in vips:
    ip = v.get('ipAddr')
    port = v.get('port')
    if ip:
        print(f"   {ip}:{port} ({v.get('serviceName')})")

# Create VIP
TEST_IP = "192.168.3.246"
TEST_PORT = 8765
print(f"\n3. Creating VIP {TEST_IP}:{TEST_PORT}...")
success, result = client.create_virtual_service(
    ip_addr=TEST_IP,
    port=TEST_PORT,
    protocol="HTTP",
    subnet_mask="255.255.255.0",
    service_name="test-client-vip"
)
print(f"   Create result: {'PASS' if success else 'FAIL'}")

# Verify VIP exists
print("\n4. Verifying VIP exists...")
vips = client.get_ip_services()
found = False
for v in vips:
    if v.get('ipAddr') == TEST_IP and str(v.get('port')) == str(TEST_PORT):
        print(f"   FOUND: {v.get('ipAddr')}:{v.get('port')} ({v.get('serviceName')})")
        found = True
        break
print(f"   Verify result: {'PASS' if found else 'FAIL'}")

# Delete VIP
print(f"\n5. Deleting VIP {TEST_IP}:{TEST_PORT}...")
deleted = client.delete_virtual_service(TEST_IP, TEST_PORT)
print(f"   Delete result: {'PASS' if deleted else 'FAIL'}")

# Verify VIP deleted
print("\n6. Verifying VIP deleted...")
vips = client.get_ip_services()
still_exists = False
for v in vips:
    if v.get('ipAddr') == TEST_IP and str(v.get('port')) == str(TEST_PORT):
        still_exists = True
        break
print(f"   Verify result: {'PASS' if not still_exists else 'FAIL'}")

client.close()

print("\n" + "="*40)
if found and deleted and not still_exists:
    print("ALL TESTS PASSED!")
else:
    print("SOME TESTS FAILED")
