"""
EdgeADC REST Client for the Octavia provider driver.
Provides synchronous methods for communicating with EdgeNexus ADC devices.
"""
from __future__ import annotations

import base64
import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

from octavia_edgeadc_driver.common import constants

LOG = logging.getLogger(__name__)


class EdgeADCClient:
    """Synchronous REST API client for EdgeADC devices."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        timeout: float = 30.0,
        verify_ssl: bool = False
    ) -> None:
        self.host = host.strip()
        self.port = port
        self.base_url = f"https://{self.host}:{self.port}"
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._guid: Optional[str] = None
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                verify=self.verify_ssl
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def login(self) -> Optional[str]:
        """Authenticate with the device and return GUID."""
        url = f"{self.base_url}{constants.API_LOGIN}"
        client = self._get_client()

        # Primary method: Base64 encoded password
        password_b64 = base64.b64encode(self.password.encode()).decode()
        auth_payload = {self.username: password_b64}

        try:
            r = client.post(
                url,
                content=str(auth_payload).replace("'", '"'),
                headers={"Content-Type": "text/plain"}
            )
            data = r.json() if r.content else {}
        except Exception as e:
            LOG.warning(f"EdgeADC login failed: {e}")
            data = {}

        guid = data.get("GUID")
        if guid:
            self._guid = guid
            client.cookies.set("GUID", guid)
            LOG.info(f"EdgeADC login successful for {self.host}")
        else:
            LOG.error(f"EdgeADC login failed for {self.host}")

        return guid

    def _ensure_login(self) -> None:
        """Ensure we have a valid session."""
        if not self._guid:
            self.login()

    def _get(self, path: str) -> Tuple[int, Any]:
        """Make a GET request."""
        self._ensure_login()
        client = self._get_client()
        url = f"{self.base_url}{path}"
        try:
            r = client.get(url)
            js = r.json() if r.content else None
        except Exception as e:
            LOG.warning(f"GET {path} failed: {e}")
            return 500, None
        return r.status_code, js

    def _post(self, path: str, payload: Dict[str, Any]) -> Tuple[int, Any]:
        """Make a POST request."""
        self._ensure_login()
        client = self._get_client()
        url = f"{self.base_url}{path}"
        try:
            r = client.post(url, json=payload)
            js = r.json() if r.content else None
        except Exception as e:
            LOG.warning(f"POST {path} failed: {e}")
            return 500, None
        return r.status_code, js

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        code, js = self._get(constants.API_SYSTEM_INFO)
        if code == 200 and isinstance(js, dict):
            return js
        return {}

    def get_ip_services(self) -> List[Dict[str, Any]]:
        """Get all IP services (VIPs)."""
        code, js = self._get(f"{constants.API_IP_SERVICES}?isPageLoad=true")
        if code != 200 or not isinstance(js, dict):
            return []

        # Parse the nested structure
        result = []
        data = js.get('data', {})
        if isinstance(data, dict):
            dataset = data.get('dataset', {})
            if isinstance(dataset, dict):
                ip_services = dataset.get('ipService', [])
                for interface_list in ip_services:
                    if isinstance(interface_list, list):
                        result.extend(interface_list)
                    elif isinstance(interface_list, dict):
                        result.append(interface_list)
        return result

    def create_virtual_service(
        self,
        ip_addr: str,
        port: int,
        protocol: str = "HTTP",
        subnet_mask: str = "255.255.255.0",
        service_name: str = ""
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Create a new Virtual IP Service (VIP)."""
        # Map Octavia protocol to EdgeADC
        edgeadc_protocol = constants.PROTOCOL_MAP.get(protocol, "TCP")

        payload = {
            "ipAddr": ip_addr,
            "port": str(port),
            "subnetMask": subnet_mask,
            "serviceType": edgeadc_protocol,
            "enabled": "1"
        }
        if service_name:
            payload["serviceName"] = service_name

        code, js = self._post(constants.API_VIP_CREATE, payload)
        success = code == 200
        LOG.info(f"EdgeADC {self.host}: Create VIP {ip_addr}:{port} - {'OK' if success else 'FAILED'}")
        return success, js

    def delete_virtual_service(self, ip_addr: str, port: int) -> bool:
        """Delete a Virtual IP Service."""
        payload = {"ipAddr": ip_addr, "port": str(port)}
        code, _ = self._post(constants.API_VIP_DELETE, payload)
        success = code == 200
        LOG.info(f"EdgeADC {self.host}: Delete VIP {ip_addr}:{port} - {'OK' if success else 'FAILED'}")
        return success

    def _get_vip_info(self, vip_ip: str, vip_port: int) -> Optional[Dict[str, Any]]:
        """Get VIP info including InterfaceID and ChannelID."""
        vips = self.get_ip_services()
        for vip in vips:
            if vip.get("ipAddr") == vip_ip and str(vip.get("port")) == str(vip_port):
                return vip
        return None

    def add_member(
        self,
        vip_ip: str,
        vip_port: int,
        member_ip: str,
        member_port: int,
        weight: int = 100
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Add a member (content server) to a VIP."""
        vip_info = self._get_vip_info(vip_ip, vip_port)
        if not vip_info:
            LOG.warning(f"VIP {vip_ip}:{vip_port} not found")
            return False, {"error": "VIP not found"}

        interface_id = vip_info.get("InterfaceID", "0")
        channel_id = vip_info.get("ChannelID", "0")

        # Step 1: Create placeholder
        init_payload = {
            "editedInterface": str(interface_id),
            "editedChannel": str(channel_id)
        }
        code1, resp1 = self._post(constants.API_SERVER_ADD_INIT, init_payload)
        if code1 != 200:
            return False, {"error": "Failed to create placeholder"}

        # Find new placeholder cId
        new_cid = self._find_placeholder_cid(resp1, vip_info.get("ChannelKey", ""))

        # Step 2: Update placeholder with actual server details
        add_payload = {
            "editedInterface": str(interface_id),
            "editedChannel": str(channel_id),
            "cId": str(new_cid),
            "statusReason": "Finding status",
            "imagePath": "images/jnpsStateGrey.gif",
            "CSActivity": "1",
            "CSIPAddr": member_ip,
            "CSPort": str(member_port),
            "CSNotes": "",
            "WeightFactor": str(weight),
            "CSMonitorEndPoint": "self",
            "contentServerGroupName": "Server Group",
            "ServerId": ""
        }

        code2, js = self._post(constants.API_SERVER_ADD_UPDATE, add_payload)
        success = code2 == 200

        if success:
            self.apply_config()

        LOG.info(f"EdgeADC {self.host}: Add member {member_ip}:{member_port} to VIP - {'OK' if success else 'FAILED'}")
        return success, js

    def _find_placeholder_cid(self, response: Dict, channel_key: str) -> int:
        """Find the cId of a newly created placeholder server."""
        if not response:
            return 0

        ip_services = response.get("data", {}).get("dataset", {}).get("ipService", [])
        max_cid = 0

        for interface_list in ip_services:
            if not isinstance(interface_list, list):
                continue
            for vip in interface_list:
                if not isinstance(vip, dict):
                    continue
                if vip.get("ChannelKey") == channel_key:
                    content_servers = vip.get("contentServer", {})
                    servers = content_servers.get("CServerId", []) if isinstance(content_servers, dict) else []
                    for server in servers:
                        if not server.get("CSIPAddr"):  # Empty = placeholder
                            cid = int(server.get("cId", 0))
                            if cid > max_cid:
                                max_cid = cid
        return max_cid

    def delete_member(
        self,
        vip_ip: str,
        vip_port: int,
        member_ip: str,
        member_port: int
    ) -> bool:
        """Delete a member from a VIP."""
        vip_info = self._get_vip_info(vip_ip, vip_port)
        if not vip_info:
            return False

        # Find the server's cId
        content_servers = vip_info.get("contentServer", {})
        servers = content_servers.get("CServerId", []) if isinstance(content_servers, dict) else []

        for server in servers:
            if server.get("CSIPAddr") == member_ip and str(server.get("CSPort")) == str(member_port):
                payload = {
                    "editedInterface": str(vip_info.get("InterfaceID", "0")),
                    "editedChannel": str(vip_info.get("ChannelID", "0")),
                    "cId": str(server.get("cId", "0"))
                }
                code, _ = self._post(constants.API_SERVER_DELETE, payload)
                success = code == 200
                LOG.info(f"EdgeADC {self.host}: Delete member {member_ip}:{member_port} - {'OK' if success else 'FAILED'}")
                return success

        LOG.warning(f"Member {member_ip}:{member_port} not found in VIP {vip_ip}:{vip_port}")
        return False

    def get_members(self, vip_ip: str, vip_port: int) -> List[Dict[str, Any]]:
        """Get all members for a VIP."""
        vip_info = self._get_vip_info(vip_ip, vip_port)
        if not vip_info:
            return []

        content_servers = vip_info.get("contentServer", {})
        servers = content_servers.get("CServerId", []) if isinstance(content_servers, dict) else []

        result = []
        for server in servers:
            if server.get("CSIPAddr"):  # Skip empty placeholders
                result.append({
                    "ip_address": server.get("CSIPAddr"),
                    "port": int(server.get("CSPort", 0)),
                    "weight": int(server.get("WeightFactor", 100)),
                    "cId": server.get("cId"),
                    "status": server.get("statusReason", "unknown")
                })
        return result

    def apply_config(self) -> bool:
        """Apply pending configuration changes."""
        code, _ = self._post(constants.API_APPLY_CONFIG, {"apply": "1"})
        return code == 200

    def update_member_weight(
        self,
        vip_ip: str,
        vip_port: int,
        member_ip: str,
        member_port: int,
        weight: int
    ) -> bool:
        """Update a member's weight."""
        vip_info = self._get_vip_info(vip_ip, vip_port)
        if not vip_info:
            return False

        content_servers = vip_info.get("contentServer", {})
        servers = content_servers.get("CServerId", []) if isinstance(content_servers, dict) else []

        for server in servers:
            if server.get("CSIPAddr") == member_ip and str(server.get("CSPort")) == str(member_port):
                payload = {
                    "editedInterface": str(vip_info.get("InterfaceID", "0")),
                    "editedChannel": str(vip_info.get("ChannelID", "0")),
                    "cId": str(server.get("cId", "0")),
                    "CSActivity": "1",
                    "CSIPAddr": member_ip,
                    "CSPort": str(member_port),
                    "WeightFactor": str(weight),
                    "CSMonitorEndPoint": "self",
                }
                code, _ = self._post(constants.API_SERVER_ADD_UPDATE, payload)
                if code == 200:
                    self.apply_config()
                    return True
                return False

        return False
