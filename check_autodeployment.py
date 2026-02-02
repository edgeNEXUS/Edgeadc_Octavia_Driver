#!/usr/bin/env python3
"""Check if AutoDeployment mode is restricting VIP creation."""
import json
import base64
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

# The device name is "AutoDeployment-Rocky-3.159" - check if there's an AutoDeployment setting
print("\n=== CHECK AUTODEPLOYMENT SETTINGS ===")

# Check various endpoints for AutoDeployment related settings
endpoints = ["/GET/1", "/GET/2", "/GET/7", "/GET/8", "/GET/11", "/GET/12", "/GET/13", "/GET/14", "/GET/15"]
for ep in endpoints:
    try:
        r = client.get(f"https://{HOST}:443{ep}")
        data = r.json()
        # Look for AutoDeployment or related settings
        for key in data.keys():
            if 'auto' in key.lower() or 'deploy' in key.lower() or 'mode' in key.lower() or 'restrict' in key.lower():
                print(f"{ep} - {key}: {data[key]}")
        if 'data' in data and isinstance(data['data'], dict):
            for key in data['data'].keys():
                if 'auto' in key.lower() or 'deploy' in key.lower() or 'mode' in key.lower():
                    print(f"{ep} - data.{key}: {data['data'][key]}")
    except Exception as e:
        pass

# Check if there's a way to see the device configuration mode
print("\n=== DEVICE INFO ===")
r = client.get(f"https://{HOST}:443/GET/9")
data = r.json()
print(f"Device Name: {data.get('Name')}")
print(f"StatusImage: {data.get('StatusImage')}")
print(f"StatusText: {data.get('StatusText')}")

# Check if maybe we need to be on a specific interface
print("\n=== INTERFACE DETAILS ===")
ip_services = data.get('data', {}).get('dataset', {}).get('ipService', [])
if ip_services and isinstance(ip_services[0], list):
    first_vip = ip_services[0][0]
    print(f"First VIP InterfaceID: {first_vip.get('InterfaceID')}")
    print(f"First VIP InterfaceKey: {first_vip.get('InterfaceKey')}")
    print(f"First VIP ChannelID: {first_vip.get('ChannelID')}")
    print(f"First VIP ChannelKey: {first_vip.get('ChannelKey')}")
    print(f"First VIP sId: {first_vip.get('sId')}")

# Try to see if there's a "new interface" or "add interface" action
print("\n=== TRY iAction=4 (might be 'add interface') ===")
payload = {
    "ipAddr": "192.168.3.240",
    "subnetMask": "255.255.255.0"
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=4", json=payload)
resp = r.json()
print(f"StatusText: {resp.get('StatusText')}")

# Check if the VIP creation response actually contains the new VIP
print("\n=== CHECK CREATE RESPONSE CAREFULLY ===")
payload = {
    "ipAddr": "192.168.3.241",
    "port": "8888",
    "subnetMask": "255.255.255.0",
    "serviceType": "HTTP",
    "serviceName": "response-check"
}
r = client.post(f"https://{HOST}:443/POST/9?iAction=1", json=payload)
resp = r.json()
print(f"StatusText: {resp.get('StatusText')}")
print(f"StatusImage: {resp.get('StatusImage')}")

# Check if the new VIP is in the response (before apply)
ip_services = resp.get('data', {}).get('dataset', {}).get('ipService', [])
print(f"\nVIPs in CREATE response:")
for iface in ip_services:
    if isinstance(iface, list):
        for vip in iface:
            ip = vip.get('ipAddr')
            port = vip.get('port')
            name = vip.get('serviceName')
            print(f"  {ip}:{port} ({name})")
            if ip == "192.168.3.241":
                print("    ^^^ OUR NEW VIP IN RESPONSE!")

client.close()
