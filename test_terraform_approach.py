#!/usr/bin/env python3
"""Test VIP creation using Terraform provider approach."""
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

# Get existing VIPs
print("\n=== EXISTING VIPS ===")
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            print(f"  {vip.get('ipAddr')}:{vip.get('port')} (sId={vip.get('sId')}, InterfaceID={vip.get('InterfaceID')}, ChannelID={vip.get('ChannelID')})")

# STEP 1: Create a blank template using iAction=3&iType=1
# This is from the Terraform provider: CreateIpServiceTemplate function
print("\n=== STEP 1: Create blank template (POST/9?iAction=3&iType=1) ===")
template_payload = {
    "editedInterface": "",
    "editedChannel": "",
    "CopyVIP": "0",
    "IpAddr": "",
    "localPortEnabledChecked": "",
    "Port": "",
    "primaryChecked": "",
    "serviceName": "blank-terraform",
    "serviceType": "",
    "subnetMask": ""
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=3&iType=1&FilterKeyword=", json=template_payload)
resp = r.json()
print(f"StatusText: {resp.get('StatusText')}")
print(f"StatusImage: {resp.get('StatusImage')}")

# Wait a moment
time.sleep(0.5)

# Check for empty VIP (template)
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
template_vip = None
print("\nLooking for empty/template VIP...")
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == "" or vip.get('serviceName') == "blank-terraform":
                print(f"  FOUND TEMPLATE: sId={vip.get('sId')}, InterfaceID={vip.get('InterfaceID')}, ChannelID={vip.get('ChannelID')}")
                template_vip = vip
                break

if template_vip:
    # STEP 2: Update the template with actual values using iAction=2&iType=1
    print("\n=== STEP 2: Update template with values (POST/9?iAction=2&iType=1) ===")
    update_payload = {
        "editedInterface": template_vip.get("InterfaceID"),
        "editedChannel": template_vip.get("ChannelID"),
        "CopyVIP": "0",
        "IpAddr": "192.168.3.245",
        "localPortEnabledChecked": "true",
        "Port": "9876",
        "primaryChecked": "Active",
        "serviceName": "octavia-terraform-test",
        "serviceType": "HTTP",
        "subnetMask": "255.255.255.0"
    }
    print(f"Payload: {json.dumps(update_payload, indent=2)}")
    r = client.post(f"https://{HOST}:443/POST/9?iAction=2&iType=1&FilterKeyword=", json=update_payload)
    resp = r.json()
    print(f"StatusText: {resp.get('StatusText')}")
    print(f"StatusImage: {resp.get('StatusImage')}")
    
    time.sleep(0.5)
    
    # Check final result
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
                if ip == "192.168.3.245" or port == "9876" or "octavia" in name.lower() if name else False:
                    print(f"  *** NEW VIP: {ip}:{port} ({name}) ***")
                    found = True
                else:
                    print(f"  {ip}:{port} ({name})")
    
    if found:
        print("\n*** SUCCESS! VIP created using Terraform approach! ***")
    else:
        print("\n*** FAILED - VIP not created ***")
else:
    print("\n*** FAILED - Template was not created ***")

client.close()
