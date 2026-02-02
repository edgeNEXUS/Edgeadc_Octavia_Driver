#!/usr/bin/env python3
"""Try to mimic GUI request format for VIP creation."""
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

# The GUI might use form data instead of JSON
print("\n=== TRY 1: Form-encoded data ===")
payload = {
    "ipAddr": "192.168.3.230",
    "port": "8765",
    "subnetMask": "255.255.255.0",
    "serviceType": "HTTP",
    "serviceName": "form-test"
}
r = client.post(
    f"https://{HOST}:443/POST/9?iAction=1",
    data=payload,  # form-encoded instead of json
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
resp = r.json()
print(f"StatusText: {resp.get('StatusText')}")

# Apply and check
r = client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})
time.sleep(1)
r = client.get(f"https://{HOST}:443/GET/9")
data = r.json()
found = False
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('port') == '8765':
                found = True
                print("*** FOUND with form-encoded! ***")
print(f"Result: {'SUCCESS' if found else 'FAILED'}")

# Try with InterfaceID=0 explicitly (matching existing VIPs)
print("\n=== TRY 2: With InterfaceID matching existing ===")
payload = {
    "InterfaceID": "0",
    "InterfaceKey": "1",
    "ipAddr": "192.168.3.231",
    "port": "8766",
    "subnetMask": "255.255.255.0",
    "serviceType": "HTTP",
    "serviceName": "interface-test",
    "enabled": "1",
    "localPortEnabledChecked": "true",
    "primaryChecked": "Active"
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=1", json=payload)
resp = r.json()
print(f"StatusText: {resp.get('StatusText')}")

r = client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})
time.sleep(1)
r = client.get(f"https://{HOST}:443/GET/9")
data = r.json()
found = False
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('port') == '8766':
                found = True
                print("*** FOUND with InterfaceID! ***")
print(f"Result: {'SUCCESS' if found else 'FAILED'}")

# Try with sId (service ID) - maybe we need to specify the next available
print("\n=== TRY 3: With sId ===")
# Get max sId from existing VIPs
r = client.get(f"https://{HOST}:443/GET/9")
data = r.json()
max_sid = 0
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            sid = int(vip.get('sId', 0))
            if sid > max_sid:
                max_sid = sid
print(f"Max existing sId: {max_sid}")

payload = {
    "sId": str(max_sid + 1),
    "ipAddr": "192.168.3.232",
    "port": "8767",
    "subnetMask": "255.255.255.0",
    "serviceType": "HTTP",
    "serviceName": "sid-test"
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=1", json=payload)
resp = r.json()
print(f"StatusText: {resp.get('StatusText')}")

r = client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})
time.sleep(1)
r = client.get(f"https://{HOST}:443/GET/9")
data = r.json()
found = False
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            if vip.get('port') == '8767':
                found = True
                print("*** FOUND with sId! ***")
print(f"Result: {'SUCCESS' if found else 'FAILED'}")

# Check if maybe we need to use a different endpoint entirely
print("\n=== TRY 4: Check /POST/10 (real servers endpoint) ===")
r = client.get(f"https://{HOST}:443/GET/10")
try:
    data = r.json()
    print(f"GET/10 keys: {list(data.keys())}")
except:
    print(f"GET/10 raw: {r.text[:200]}")

client.close()
