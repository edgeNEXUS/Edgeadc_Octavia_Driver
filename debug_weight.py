#!/usr/bin/env python3
"""Debug weight update."""
import sys
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

# Create a test VIP
print("\n=== Creating test VIP ===")
template_payload = {
    "editedInterface": "", "editedChannel": "", "CopyVIP": "0",
    "ipAddr": "", "localPortEnabledChecked": "", "port": "",
    "primaryChecked": "", "serviceName": "", "serviceType": "", "subnetMask": ""
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=3&iType=1&FilterKeyword=", json=template_payload)
print(f"Template created: {r.json().get('StatusText')}")

time.sleep(0.3)

# Find template
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
template = None
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if not vip.get('ipAddr'):
                template = vip
                break

if template:
    update_payload = {
        "editedInterface": str(template.get("InterfaceID")),
        "editedChannel": str(template.get("ChannelID")),
        "CopyVIP": "0", "ipAddr": "192.168.3.248", "localPortEnabledChecked": "true",
        "port": "7777", "primaryChecked": "Active", "serviceName": "weight-test",
        "serviceType": "HTTP", "subnetMask": "255.255.255.0"
    }
    r = client.post(f"https://{HOST}:443/POST/9?iAction=2&iType=1&FilterKeyword=", json=update_payload)
    print(f"VIP updated: {r.json().get('StatusText')}")

# Apply
client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})
time.sleep(0.3)

# Find the VIP
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
test_vip = None
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == "192.168.3.248":
                test_vip = vip
                print(f"Found VIP: InterfaceID={vip.get('InterfaceID')}, ChannelID={vip.get('ChannelID')}, ChannelKey={vip.get('ChannelKey')}")
                break

if not test_vip:
    print("VIP not found!")
    sys.exit(1)

# Add a member
print("\n=== Adding member ===")
init_payload = {
    "editedInterface": str(test_vip.get("InterfaceID")),
    "editedChannel": str(test_vip.get("ChannelID"))
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=3&iType=3&FilterKeyword=", json=init_payload)
print(f"Placeholder created: {r.json().get('StatusText')}")

# Find cId
time.sleep(0.3)
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
cid = None
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == "192.168.3.248":
                cs = vip.get('contentServer', {})
                servers = cs.get('CServerId', [])
                if isinstance(servers, dict):
                    servers = [servers]
                for srv in servers:
                    if not srv.get('CSIPAddr'):
                        cid = srv.get('cId')
                        print(f"Found placeholder cId={cid}")
                        break

# Update member
add_payload = {
    "editedInterface": str(test_vip.get("InterfaceID")),
    "editedChannel": str(test_vip.get("ChannelID")),
    "cId": str(cid),
    "statusReason": "Finding status",
    "imagePath": "images/jnpsStateGrey.gif",
    "CSActivity": "1",
    "CSIPAddr": "10.0.0.99",
    "CSPort": "8888",
    "CSNotes": "",
    "WeightFactor": "100",
    "CSMonitorEndPoint": "self",
    "contentServerGroupName": "Server Group",
    "ServerId": ""
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=2&iType=2&FilterKeyword=", json=add_payload)
print(f"Member added: {r.json().get('StatusText')}")

client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})
time.sleep(0.3)

# Check current weight
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == "192.168.3.248":
                cs = vip.get('contentServer', {})
                servers = cs.get('CServerId', [])
                if isinstance(servers, dict):
                    servers = [servers]
                for srv in servers:
                    if srv.get('CSIPAddr') == "10.0.0.99":
                        print(f"\nCurrent member: cId={srv.get('cId')}, weight={srv.get('WeightFactor')}")
                        cid = srv.get('cId')

# Now try to update weight
print("\n=== Updating weight to 50 ===")
weight_payload = {
    "editedInterface": str(test_vip.get("InterfaceID")),
    "editedChannel": str(test_vip.get("ChannelID")),
    "cId": str(cid),
    "CSActivity": "1",
    "CSIPAddr": "10.0.0.99",
    "CSPort": "8888",
    "WeightFactor": "50",
    "CSMonitorEndPoint": "self"
}
print(f"Payload: {json.dumps(weight_payload)}")
r = client.post(f"https://{HOST}:443/POST/9?iAction=2&iType=2&FilterKeyword=", json=weight_payload)
resp = r.json()
print(f"Response: {json.dumps(resp)}")

client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})
time.sleep(0.5)

# Check weight again
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == "192.168.3.248":
                cs = vip.get('contentServer', {})
                servers = cs.get('CServerId', [])
                if isinstance(servers, dict):
                    servers = [servers]
                for srv in servers:
                    if srv.get('CSIPAddr') == "10.0.0.99":
                        print(f"\nAfter update: weight={srv.get('WeightFactor')}")

# Cleanup
print("\n=== Cleanup ===")
# Delete member
del_payload = {
    "editedInterface": str(test_vip.get("InterfaceID")),
    "editedChannel": str(test_vip.get("ChannelID")),
    "cId": str(cid)
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=3&iType=5&FilterKeyword=", json=del_payload)
print(f"Member deleted: {r.json().get('StatusText')}")

# Delete VIP
vip_del_payload = {
    "editedInterface": str(test_vip.get("InterfaceID")),
    "editedChannel": str(test_vip.get("ChannelID"))
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=3&iType=4&FilterKeyword=", json=vip_del_payload)
print(f"VIP deleted: {r.json().get('StatusText')}")

client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})

client.close()
