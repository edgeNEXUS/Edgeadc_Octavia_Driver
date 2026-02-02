#!/usr/bin/env python3
"""Debug - check network interfaces and try creating VIP on existing interface IP."""
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

# Get network interfaces
print("\n=== NETWORK INTERFACES (/GET/6) ===")
r = client.get(f"https://{HOST}:443/GET/6")
data = r.json()
print(f"Keys: {list(data.keys())}")
if 'data' in data:
    print(f"data keys: {list(data['data'].keys()) if isinstance(data['data'], dict) else 'not dict'}")

# Check GET/3 for interface info
print("\n=== HARDWARE/INTERFACE INFO (/GET/3) ===")
r = client.get(f"https://{HOST}:443/GET/3")
data = r.json()
print(f"Keys: {list(data.keys())}")

# Check GET/5 for system info
print("\n=== SYSTEM INFO (/GET/5) ===")
r = client.get(f"https://{HOST}:443/GET/5")
data = r.json()
if 'HardwareGrid' in data:
    rows = data.get('HardwareGrid', {}).get('dataset', {}).get('row', [])
    for row in rows:
        print(f"  Interface {row.get('id')}: {row.get('ethName')}")

# All existing VIPs use 192.168.3.161 - let's try creating on a NEW port on that IP
print("\n=== TRY: Create new port on existing VIP IP (192.168.3.161) ===")
# First check what ports are used
r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
data = r.json()
used_ports = []
for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
    if isinstance(iface, list):
        for vip in iface:
            used_ports.append(vip.get('port'))
print(f"Used ports on 192.168.3.161: {used_ports}")

# Try port 9999
new_port = "9999"
if new_port not in used_ports:
    print(f"\nCreating VIP on 192.168.3.161:{new_port}...")
    payload = {
        "ipAddr": "192.168.3.161",
        "port": new_port,
        "subnetMask": "255.255.255.0",
        "serviceType": "HTTP",
        "serviceName": "octavia-test-new-port"
    }
    r = client.post(f"https://{HOST}:443/POST/9?iAction=1", json=payload)
    resp = r.json()
    print(f"StatusText: {resp.get('StatusText')}")
    
    # Apply
    r = client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})
    time.sleep(2)
    
    # Check
    r = client.get(f"https://{HOST}:443/GET/9?isPageLoad=true")
    data = r.json()
    found = False
    print("\nVIPs after create:")
    for iface in data.get('data', {}).get('dataset', {}).get('ipService', []):
        if isinstance(iface, list):
            for vip in iface:
                ip = vip.get('ipAddr')
                port = vip.get('port')
                name = vip.get('serviceName')
                if port == new_port:
                    found = True
                    print(f"  *** {ip}:{port} ({name}) - NEW! ***")
                else:
                    print(f"  {ip}:{port} ({name})")
    
    if found:
        print("\n*** SUCCESS! VIP created on existing IP with new port! ***")
        # Cleanup
        r = client.post(f"https://{HOST}:443/POST/9?iAction=3", json={"ipAddr": "192.168.3.161", "port": new_port})
        r = client.post(f"https://{HOST}:443/POST/5?iAction=1", json={"apply": "1"})
        print("Cleaned up test VIP")
    else:
        print("\n*** FAILED - VIP not created ***")

client.close()
