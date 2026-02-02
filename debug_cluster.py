#!/usr/bin/env python3
"""Check if EdgeADC is in cluster/read-only mode."""
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
login_resp = r.json()
guid = login_resp.get("GUID")
client.cookies.set("GUID", guid)
print(f"Login response: {json.dumps(login_resp)}")

# Check cluster status
print("\n=== CLUSTER STATUS (/GET/30) ===")
r = client.get(f"https://{HOST}:443/GET/30")
try:
    data = r.json()
    print(f"Response: {json.dumps(data, indent=2)[:1000]}")
except:
    print(f"Raw: {r.text[:500]}")

# Check if there's a "mode" or "state" in system info
print("\n=== SYSTEM STATE ===")
for endpoint in ["/GET/1", "/GET/2", "/GET/5"]:
    print(f"\n--- {endpoint} ---")
    r = client.get(f"https://{HOST}:443{endpoint}")
    try:
        data = r.json()
        # Look for mode/state/cluster related fields
        for key in ['Mode', 'mode', 'State', 'state', 'Cluster', 'cluster', 'ReadOnly', 'readonly', 'Primary', 'primary', 'Standby', 'standby', 'Role', 'role']:
            if key in data:
                print(f"  {key}: {data[key]}")
        # Check nested data
        if 'data' in data and isinstance(data['data'], dict):
            for key in data['data'].keys():
                if any(x in key.lower() for x in ['mode', 'state', 'cluster', 'role', 'primary', 'standby']):
                    print(f"  data.{key}: {data['data'][key]}")
    except:
        print(f"  Could not parse: {r.text[:200]}")

# Check the Name field from login - it says "AutoDeployment-Rocky-3.159"
print("\n=== DEVICE NAME ===")
r = client.get(f"https://{HOST}:443/GET/9")
data = r.json()
print(f"Name: {data.get('Name')}")

# Try a different approach - maybe we need to use a different iAction
print("\n=== TRY DIFFERENT iAction VALUES ===")
for action in [1, 2, 4, 5]:
    payload = {
        "ipAddr": "192.168.3.250",
        "port": str(7770 + action),
        "subnetMask": "255.255.255.0",
        "serviceType": "HTTP",
        "serviceName": f"test-action-{action}"
    }
    r = client.post(f"https://{HOST}:443/POST/9?iAction={action}", json=payload)
    resp = r.json()
    print(f"iAction={action}: success={resp.get('success')}, StatusText={resp.get('StatusText')[:50] if resp.get('StatusText') else 'N/A'}")

client.close()
