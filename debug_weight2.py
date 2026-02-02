#!/usr/bin/env python3
"""Debug weight update with all required fields."""
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

# Use existing VIP 192.168.3.161:80 (WAF Ingress) for testing
# First add a test member
print("\n=== Adding test member to existing VIP ===")
# Get VIP info
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
test_vip = None
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == "192.168.3.161" and vip.get('port') == "80":
                test_vip = vip
                print(f"Found VIP: InterfaceID={vip.get('InterfaceID')}, ChannelID={vip.get('ChannelID')}")
                break

if not test_vip:
    print("VIP not found!")
    sys.exit(1)

# Add placeholder
init_payload = {
    "editedInterface": str(test_vip.get("InterfaceID")),
    "editedChannel": str(test_vip.get("ChannelID"))
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=3&iType=3&FilterKeyword=", json=init_payload)
print(f"Placeholder: {r.json().get('StatusText')}")

time.sleep(0.3)

# Find cId
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
cid = None
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == "192.168.3.161" and vip.get('port') == "80":
                cs = vip.get('contentServer', {})
                servers = cs.get('CServerId', [])
                if isinstance(servers, dict):
                    servers = [servers]
                for srv in servers:
                    if not srv.get('CSIPAddr'):
                        cid = srv.get('cId')
                        print(f"Placeholder cId={cid}")
                        break

# Add member with weight 100
add_payload = {
    "editedInterface": str(test_vip.get("InterfaceID")),
    "editedChannel": str(test_vip.get("ChannelID")),
    "cId": str(cid),
    "CSActivity": "1",
    "CSIPAddr": "10.99.99.99",
    "CSPort": "9999",
    "WeightFactor": "100",
    "imagePath": "images/jnpsStateGrey.gif",
    "statusReason": "Finding status",
    "CSNotes": "",
    "contentServerGroupName": "Server Group",
    "ServerId": "",
    "CSMonitorEndPoint": "self"
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=2&iType=2&FilterKeyword=", json=add_payload)
print(f"Member added: {r.json().get('StatusText')}")

client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})
time.sleep(0.5)

# Get current state
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == "192.168.3.161" and vip.get('port') == "80":
                cs = vip.get('contentServer', {})
                servers = cs.get('CServerId', [])
                if isinstance(servers, dict):
                    servers = [servers]
                for srv in servers:
                    if srv.get('CSIPAddr') == "10.99.99.99":
                        cid = srv.get('cId')
                        print(f"\nCurrent: cId={cid}, weight={srv.get('WeightFactor')}")

# Update with ALL fields from UpdateServer model
print("\n=== Updating weight to 50 with ALL fields ===")
update_payload = {
    "editedInterface": str(test_vip.get("InterfaceID")),
    "editedChannel": str(test_vip.get("ChannelID")),
    "cId": str(cid),
    "CSActivity": "1",
    "CSIPAddr": "10.99.99.99",
    "CSPort": "9999",
    "WeightFactor": "50",
    "imagePath": "images/jnpsStateGrey.gif",
    "statusReason": "Finding status",
    "CSNotes": "",
    "contentServerGroupName": "Server Group",
    "ServerId": "",
    "CSMonitorEndPoint": "self"
}
print(f"Payload: {json.dumps(update_payload, indent=2)}")
r = client.post(f"https://{HOST}:443/POST/9?iAction=2&iType=2&FilterKeyword=", json=update_payload)
resp = r.json()
print(f"Response: StatusText={resp.get('StatusText')}, StatusImage={resp.get('StatusImage')}")

client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})
time.sleep(0.5)

# Verify
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == "192.168.3.161" and vip.get('port') == "80":
                cs = vip.get('contentServer', {})
                servers = cs.get('CServerId', [])
                if isinstance(servers, dict):
                    servers = [servers]
                for srv in servers:
                    if srv.get('CSIPAddr') == "10.99.99.99":
                        print(f"\nAfter update: weight={srv.get('WeightFactor')}")
                        final_weight = srv.get('WeightFactor')

# Cleanup
print("\n=== Cleanup ===")
del_payload = {
    "editedInterface": str(test_vip.get("InterfaceID")),
    "editedChannel": str(test_vip.get("ChannelID")),
    "cId": str(cid)
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=3&iType=5&FilterKeyword=", json=del_payload)
print(f"Member deleted: {r.json().get('StatusText')}")
client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})

client.close()

if final_weight == "50":
    print("\n*** SUCCESS - Weight updated! ***")
else:
    print(f"\n*** FAILED - Weight is still {final_weight} ***")
