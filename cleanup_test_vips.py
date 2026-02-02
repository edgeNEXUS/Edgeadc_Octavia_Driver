#!/usr/bin/env python3
"""Cleanup any test VIPs from previous runs."""
import sys
sys.path.insert(0, '/software/octavia-edgeadc-driver')
from octavia_edgeadc_driver.api.edgeadc_client import EdgeADCClient

client = EdgeADCClient("192.168.3.159", "admin", "1nSpa1n1234")
client.login()

# Clean up any VIPs in our test range
test_prefixes = ["192.168.3.23", "192.168.3.24"]
vips = client.get_ip_services()
for v in vips:
    ip = v.get('ipAddr', '')
    port = v.get('port', '')
    if any(ip.startswith(p) for p in test_prefixes):
        print(f"Deleting test VIP: {ip}:{port}")
        client.delete_virtual_service(ip, int(port))

# Also clean up any blank templates
vips = client.get_ip_services()
for v in vips:
    if not v.get('ipAddr'):
        print(f"Deleting blank template: InterfaceID={v.get('InterfaceID')}")
        from octavia_edgeadc_driver.common import constants
        client._post(constants.API_VIP_DELETE, {
            "editedInterface": str(v.get("InterfaceID")),
            "editedChannel": str(v.get("ChannelID"))
        })

client.apply_config()
client.close()
print("Cleanup complete")
