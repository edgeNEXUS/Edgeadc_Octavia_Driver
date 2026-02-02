"""
Unit tests for EdgeADC REST client.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import base64


class TestEdgeADCClientInit:
    """Tests for EdgeADCClient initialization."""

    def test_init(self):
        """Test client initialization."""
        from octavia_edgeadc_driver.api.edgeadc_client import EdgeADCClient
        client = EdgeADCClient(
            host="192.168.1.100",
            username="admin",
            password="testpass",
            port=443,
            timeout=30,
            verify_ssl=False
        )
        assert client.host == "192.168.1.100"
        assert client.username == "admin"
        assert client.port == 443
        assert client.base_url == "https://192.168.1.100:443"
        client.close()

    def test_encode_password(self):
        """Test password encoding."""
        encoded = base64.b64encode("testpass".encode()).decode()
        assert encoded == "dGVzdHBhc3M="


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

    def test_protocol_map_tcp(self):
        """Test TCP protocol mapping."""
        from octavia_edgeadc_driver.common.constants import PROTOCOL_MAP
        assert PROTOCOL_MAP["TCP"] == "TCP"

    def test_protocol_map_udp(self):
        """Test UDP protocol mapping."""
        from octavia_edgeadc_driver.common.constants import PROTOCOL_MAP
        assert PROTOCOL_MAP["UDP"] == "UDP"


class TestLBAlgorithmMapping:
    """Tests for load balancing algorithm mapping."""

    def test_lb_algorithm_map_round_robin(self):
        """Test ROUND_ROBIN algorithm mapping."""
        from octavia_edgeadc_driver.common.constants import LB_ALGORITHM_MAP
        assert LB_ALGORITHM_MAP["ROUND_ROBIN"] == "RoundRobin"

    def test_lb_algorithm_map_least_connections(self):
        """Test LEAST_CONNECTIONS algorithm mapping."""
        from octavia_edgeadc_driver.common.constants import LB_ALGORITHM_MAP
        assert LB_ALGORITHM_MAP["LEAST_CONNECTIONS"] == "LeastConnections"

    def test_lb_algorithm_map_source_ip(self):
        """Test SOURCE_IP algorithm mapping."""
        from octavia_edgeadc_driver.common.constants import LB_ALGORITHM_MAP
        assert LB_ALGORITHM_MAP["SOURCE_IP"] == "SourceIP"


class TestAPIEndpoints:
    """Tests for API endpoint constants."""

    def test_api_login(self):
        """Test login endpoint."""
        from octavia_edgeadc_driver.common.constants import API_LOGIN
        assert API_LOGIN == '/POST/32'

    def test_api_ip_services(self):
        """Test IP services endpoint."""
        from octavia_edgeadc_driver.common.constants import API_IP_SERVICES
        assert API_IP_SERVICES == '/GET/9'

    def test_api_apply(self):
        """Test apply config endpoint."""
        from octavia_edgeadc_driver.common.constants import API_APPLY_CONFIG
        assert API_APPLY_CONFIG == '/POST/5?iAction=1'
