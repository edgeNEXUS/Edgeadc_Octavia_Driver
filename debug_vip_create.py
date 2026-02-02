#!/usr/bin/env python3
"""Debug VIP creation - compare with what works."""
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

# Get an existing VIP to see all its fields
print("\n=== EXISTING VIP STRUCTURE ===")
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
ip_services = data.get('data', {}).get('dataset', {}).get('ipService', [])
if ip_services and isinstance(ip_services[0], list) and len(ip_services[0]) > 0:
    existing_vip = ip_services[0][0]
    print("Fields in existing VIP:")
    for key in sorted(existing_vip.keys()):
        val = existing_vip.get(key)
        if not isinstance(val, (dict, list)):
            print(f"  {key}: {val}")

# Try different create approaches
print("\n=== TRY 1: Minimal payload ===")
payload1 = {
    "ipAddr": "192.168.3.220",
    "port": "7777",
    "subnetMask": "255.255.255.0",
    "serviceType": "HTTP"
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=1", json=payload1)
resp = r.json()
print(f"Payload: {json.dumps(payload1)}")
print(f"StatusText: {resp.get('StatusText')}")

# Check if VIP appears in response
found_in_resp = False
for iface in resp.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == '192.168.3.220':
                found_in_resp = True
                print("*** VIP FOUND IN CREATE RESPONSE! ***")
print(f"VIP in response: {found_in_resp}")

# Apply config
r = client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})
time.sleep(1)

# Check fresh list
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
found_in_list = False
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == '192.168.3.220':
                found_in_list = True
                print("*** VIP FOUND IN FRESH LIST! ***")
print(f"VIP in fresh list: {found_in_list}")

print("\n=== TRY 2: With more fields matching existing VIP ===")
payload2 = {
    "ipAddr": "192.168.3.221",
    "port": "7778",
    "subnetMask": "255.255.255.0",
    "serviceType": "HTTP",
    "serviceName": "octavia-test",
    "loadBalancingPolicy": "RoundRobin",
    "serverMonitoring": "Connect",
    "connectivity": "managed",
    "enabled": "1",
    "primaryChecked": "Active"
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=1", json=payload2)
resp = r.json()
print(f"Payload: {json.dumps(payload2)}")
print(f"StatusText: {resp.get('StatusText')}")

# Apply and check
r = client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})
time.sleep(1)
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
found = False
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('ipAddr') == '192.168.3.221':
                found = True
                print("*** VIP FOUND! ***")
print(f"VIP in list: {found}")

print("\n=== TRY 3: Check if maybe we need to use text/plain content type ===")
payload3 = {
    "ipAddr": "192.168.3.222",
    "port": "7779",
    "subnetMask": "255.255.255.0",
    "serviceType": "HTTP"
}
r = client.post(
    f"https://{HOST}:443/POST/9?iAction=1",
    content=json.dumps(payload3),
    headers={"Content-Type": "text/plain"}
)
resp = r.json()
print(f"StatusText: {resp.get('StatusText')}")

r = client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})
time.sleep(1)
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
found = False
print("\nAll VIPs now:")
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            ip = vip.get('ipAddr')
            port = vip.get('port')
            name = vip.get('serviceName')
            print(f"  {ip}:{port} ({name})")
            if ip in ['192.168.3.220', '192.168.3.221', '192.168.3.222']:
                found = True
                print("    ^^^ NEW VIP!")

if not found:
    print("\n*** NO NEW VIPS CREATED - checking if there's an error in response ***")
    # Maybe the API silently fails - let's check the StatusImage
    print(f"Last response StatusImage: {resp.get('StatusImage')}")

client.close()
