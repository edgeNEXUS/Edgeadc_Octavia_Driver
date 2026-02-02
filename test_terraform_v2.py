#!/usr/bin/env python3
"""Test VIP creation using Terraform provider approach with correct field names."""
import json
import base64
import time
import httpx

HOST = "192.168.3.159"
USER = "admin"
PASS = "1nSpa1n1234"

client = httpx.Client(timeout=30, verify=False)

# Login
password_b64 = base64.b64encode(PASS.encode()).decode()
auth_payload = f'{{"{USER}":"{password_b64}"}}'
r = client.post(f"https://{HOST}:443/POST/32", content=auth_payload, headers={"Content-Type": "text/plain"})
guid = r.json().get("GUID")
client.cookies.set("GUID", guid)
print(f"Logged in: {guid}")

# First, check if there's already a blank template and clean it up
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
print("\n=== CHECKING FOR EXISTING TEMPLATE ===")
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == "":
                print(f"  Found existing blank template: sId={vip.get('sId')}, InterfaceID={vip.get('InterfaceID')}, ChannelID={vip.get('ChannelID')}")
                # Use this one instead of creating a new one
                template_vip = vip
                break

# If no existing template, create one
print("\n=== STEP 1: Create blank template (POST/9?iAction=3&iType=1) ===")
template_payload = {
    "editedInterface": "",
    "editedChannel": "",
    "CopyVIP": "0",
    "ipAddr": "",  # lowercase!
    "localPortEnabledChecked": "",
    "port": "",  # lowercase!
    "primaryChecked": "",
    "serviceName": "blank-terraform",
    "serviceType": "",
    "subnetMask": ""
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=3&iType=1&FilterKeyword=", json=template_payload)
resp = r.json()
print(f"StatusText: {resp.get('StatusText')}")

time.sleep(0.5)

# Find the template
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
template_vip = None
print("\nLooking for empty/template VIP...")
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == "":
                print(f"  FOUND TEMPLATE: sId={vip.get('sId')}, InterfaceID={vip.get('InterfaceID')}, ChannelID={vip.get('ChannelID')}")
                template_vip = vip

if template_vip:
    # STEP 2: Update with correct lowercase field names
    print("\n=== STEP 2: Update template (POST/9?iAction=2&iType=1) ===")
    update_payload = {
        "editedInterface": str(template_vip.get("InterfaceID")),
        "editedChannel": str(template_vip.get("ChannelID")),
        "CopyVIP": "0",
        "ipAddr": "192.168.3.245",  # lowercase
        "localPortEnabledChecked": "true",
        "port": "9876",  # lowercase
        "primaryChecked": "Active",
        "serviceName": "octavia-tf-test",
        "serviceType": "HTTP",
        "subnetMask": "255.255.255.0"
    }
    print(f"Payload: {json.dumps(update_payload)}")
    r = client.post(f"https://{HOST}:443/POST/9?iAction=2&iType=1&FilterKeyword=", json=update_payload)
    resp = r.json()
    print(f"StatusText: {resp.get('StatusText')}")
    print(f"StatusImage: {resp.get('StatusImage')}")
    
    time.sleep(0.5)
    
    # Check result
    print("\n=== FINAL VIPs ===")
    r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
    data = r.json()
    found = False
    for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
        if isinstance(iface, list):
            for vip in iface:
                ip = vip.get('ipAddr')
                port = vip.get('port')
                name = vip.get('serviceName')
                sid = vip.get('sId')
                if ip == "192.168.3.245" or port == "9876":
                    print(f"  *** NEW VIP: {ip}:{port} ({name}) sId={sid} ***")
                    found = True
                elif ip:
                    print(f"  {ip}:{port} ({name})")
                else:
                    print(f"  [blank template] sId={sid}")
    
    if found:
        print("\n*** SUCCESS! VIP created using Terraform approach! ***")
        # Clean up - delete the test VIP
        print("\nCleaning up test VIP...")
        delete_payload = {
            "editedInterface": str(template_vip.get("InterfaceID")),
            "editedChannel": str(template_vip.get("ChannelID"))
        }
        r = client.post(f"https://{HOST}:443/POST/9?iAction=3&iType=4&FilterKeyword=", json=delete_payload)
        print(f"Delete result: {r.json().get('StatusText')}")
    else:
        print("\n*** FAILED - VIP not created ***")
else:
    print("\n*** FAILED - No template found ***")

client.close()
