"""
Unit tests for EdgeADC REST client.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import base64

from octavia_edgeadc_driver.api.edgeadc_client import EdgeADCClient


class TestEdgeADCClient:
    """Tests for EdgeADCClient class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = EdgeADCClient(
            host="192.168.1.100",
            username="admin",
            password="testpass",
            port=443,
            timeout=30,
            verify_ssl=False
        )

    def test_init(self):
        """Test client initialization."""
        assert self.client.host == "192.168.1.100"
        assert self.client.username == "admin"
        assert self.client.port == 443
        assert self.client.base_url == "https://192.168.1.100:443"

    def test_encode_password(self):
        """Test password encoding."""
        encoded = base64.b64encode("testpass".encode()).decode()
        assert encoded == "dGVzdHBhc3M="

    @patch('httpx.Client')
    def test_login_success(self, mock_client_class):
        """Test successful login."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "LoginStatus": "OK",
            "UserName": "admin",
            "GUID": "test-guid-12345"
        }
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = Mock(return_value=False)
        
        # Create new client to use mocked httpx
        with patch.object(self.client, '_session', mock_client):
            self.client._session = mock_client
            result = self.client.login()
        
        assert self.client.guid == "test-guid-12345"

    @patch('httpx.Client')
    def test_login_failure(self, mock_client_class):
        """Test failed login."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "LoginStatus": "Failed",
            "UserName": "",
            "GUID": ""
        }
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        
        with patch.object(self.client, '_session', mock_client):
            result = self.client.login()
        
        assert result is False

    def test_get_headers_without_guid(self):
        """Test headers without GUID."""
        headers = self.client._get_headers()
        assert "Content-Type" in headers
        assert "Cookie" not in headers

    def test_get_headers_with_guid(self):
        """Test headers with GUID."""
        self.client.guid = "test-guid"
        headers = self.client._get_headers()
        assert headers["Cookie"] == "GUID=test-guid"


class TestVirtualServiceOperations:
    """Tests for virtual service operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = EdgeADCClient(
            host="192.168.1.100",
            username="admin",
            password="testpass"
        )
        self.client.guid = "test-guid"

    @patch.object(EdgeADCClient, '_make_request')
    def test_create_virtual_service(self, mock_request):
        """Test creating a virtual service."""
        mock_request.return_value = (True, {"status": "ok"})
        
        success, result = self.client.create_virtual_service(
            ip_addr="10.0.0.100",
            port=80,
            protocol="HTTP",
            subnet_mask="255.255.255.0",
            service_name="test-vip"
        )
        
        assert success is True
        mock_request.assert_called()

    @patch.object(EdgeADCClient, '_make_request')
    def test_delete_virtual_service(self, mock_request):
        """Test deleting a virtual service."""
        mock_request.return_value = (True, {"status": "ok"})
        
        success = self.client.delete_virtual_service("10.0.0.100", 80)
        
        assert success is True


class TestMemberOperations:
    """Tests for member operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = EdgeADCClient(
            host="192.168.1.100",
            username="admin",
            password="testpass"
        )
        self.client.guid = "test-guid"

    @patch.object(EdgeADCClient, '_make_request')
    @patch.object(EdgeADCClient, 'apply_config')
    def test_add_member(self, mock_apply, mock_request):
        """Test adding a member."""
        mock_request.return_value = (True, {"status": "ok"})
        mock_apply.return_value = True
        
        success, result = self.client.add_member(
            vip_ip="10.0.0.100",
            vip_port=80,
            member_ip="10.0.0.10",
            member_port=8080,
            weight=100
        )
        
        assert success is True

    @patch.object(EdgeADCClient, '_make_request')
    def test_delete_member(self, mock_request):
        """Test deleting a member."""
        mock_request.return_value = (True, {"status": "ok"})
        
        success = self.client.delete_member(
            vip_ip="10.0.0.100",
            vip_port=80,
            member_ip="10.0.0.10",
            member_port=8080
        )
        
        assert success is True


class TestProtocolMapping:
    """Tests for protocol mapping."""

    def test_protocol_map_http(self):
        """Test HTTP protocol mapping."""
        from octavia_edgeadc_driver.common.constants import PROTOCOL_MAP
        assert PROTOCOL_MAP["HTTP"] == "HTTP"

    def test_protocol_map_https(self):
        """Test HTTPS protocol mapping."""
        from octavia_edgeadc_driver.common.constants import PROTOCOL_MAP
        assert PROTOCOL_MAP["HTTPS"] == "HTTPS"

    def test_protocol_map_terminated_https(self):
        """Test TERMINATED_HTTPS protocol mapping."""
        from octavia_edgeadc_driver.common.constants import PROTOCOL_MAP
        assert PROTOCOL_MAP["TERMINATED_HTTPS"] == "HTTPS"

    def test_lb_algorithm_map(self):
        """Test load balancing algorithm mapping."""
        from octavia_edgeadc_driver.common.constants import LB_ALGORITHM_MAP
        assert LB_ALGORITHM_MAP["ROUND_ROBIN"] == "RoundRobin"
        assert LB_ALGORITHM_MAP["LEAST_CONNECTIONS"] == "LeastConnections"
