#!/usr/bin/env python3
"""
Integration test for EdgeADC Octavia Driver.
Tests the REST client against a real EdgeADC appliance.
"""
import sys
sys.path.insert(0, '/software/octavia-edgeadc-driver')

from octavia_edgeadc_driver.api.edgeadc_client import EdgeADCClient

# Test configuration
EDGEADC_HOST = "192.168.3.159"
EDGEADC_USER = "admin"
EDGEADC_PASS = "1nSpa1n1234"

# Test VIP configuration
TEST_VIP_IP = "192.168.100.200"
TEST_VIP_PORT = 8888
TEST_VIP_NAME = "octavia-test-vip"
TEST_MEMBER_IP = "192.168.100.10"
TEST_MEMBER_PORT = 80

def test_client():
    print("=" * 60)
    print("EdgeADC Octavia Driver - Integration Test")
    print("=" * 60)
    print(f"Target: {EDGEADC_HOST}")
    print()

    # Create client
    client = EdgeADCClient(
        host=EDGEADC_HOST,
        username=EDGEADC_USER,
        password=EDGEADC_PASS,
        port=443,
        timeout=30,
        verify_ssl=False
    )

    # Test 1: Login
    print("[1/7] Testing login...")
    try:
        guid = client.login()
        if guid:
            print(f"  ✓ Login successful! GUID: {guid[:20]}...")
        else:
            print("  ✗ Login failed - no GUID returned")
            return False
    except Exception as e:
        print(f"  ✗ Login error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Get system info
    print("\n[2/7] Getting system info...")
    try:
        info = client.get_system_info()
        if info:
            print(f"  ✓ System info retrieved")
            print(f"    Version: {info.get('Version', 'N/A')}")
        else:
            print("  ! No system info returned")
    except Exception as e:
        print(f"  ! Error getting system info: {e}")

    # Test 3: Get existing VIPs
    print("\n[3/7] Getting existing IP services...")
    try:
        services = client.get_ip_services()
        print(f"  ✓ Found {len(services)} IP services")
        if len(services) > 0:
            for svc in services[:3]:  # Show first 3
                if isinstance(svc, dict):
                    print(f"    - {svc.get('IPAddress', 'N/A')}:{svc.get('Port', 'N/A')} ({svc.get('ServiceName', 'N/A')})")
    except Exception as e:
        print(f"  ! Error getting services: {e}")

    # Test 4: Create a test VIP
    print(f"\n[4/7] Creating test VIP: {TEST_VIP_IP}:{TEST_VIP_PORT}...")
    try:
        success, result = client.create_virtual_service(
            ip_addr=TEST_VIP_IP,
            port=TEST_VIP_PORT,
            protocol="HTTP",
            subnet_mask="255.255.255.0",
            service_name=TEST_VIP_NAME
        )
        if success:
            print(f"  ✓ VIP created successfully")
        else:
            print(f"  ! VIP creation returned: {result}")
    except Exception as e:
        print(f"  ✗ Error creating VIP: {e}")
        import traceback
        traceback.print_exc()

    # Test 5: Add a member
    print(f"\n[5/7] Adding member: {TEST_MEMBER_IP}:{TEST_MEMBER_PORT}...")
    try:
        success, result = client.add_member(
            vip_ip=TEST_VIP_IP,
            vip_port=TEST_VIP_PORT,
            member_ip=TEST_MEMBER_IP,
            member_port=TEST_MEMBER_PORT,
            weight=100
        )
        if success:
            print(f"  ✓ Member added successfully")
        else:
            print(f"  ! Member add returned: {result}")
    except Exception as e:
        print(f"  ✗ Error adding member: {e}")
        import traceback
        traceback.print_exc()

    # Test 6: Get members
    print(f"\n[6/7] Getting members for VIP...")
    try:
        members = client.get_members(TEST_VIP_IP, TEST_VIP_PORT)
        print(f"  ✓ Found {len(members)} members")
        for m in members:
            if isinstance(m, dict):
                print(f"    - {m.get('ContentServer', m.get('IPAddress', 'N/A'))}:{m.get('Port', 'N/A')}")
    except Exception as e:
        print(f"  ! Error getting members: {e}")

    # Test 7: Cleanup - Delete VIP
    print(f"\n[7/7] Cleaning up - deleting test VIP...")
    try:
        success = client.delete_virtual_service(TEST_VIP_IP, TEST_VIP_PORT)
        if success:
            print(f"  ✓ VIP deleted successfully")
        else:
            print(f"  ! VIP deletion returned false")
    except Exception as e:
        print(f"  ✗ Error deleting VIP: {e}")

    # Close client
    client.close()

    print("\n" + "=" * 60)
    print("Integration test complete!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_client()
