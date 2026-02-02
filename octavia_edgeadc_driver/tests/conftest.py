"""
Pytest configuration and fixtures for EdgeADC driver tests.
"""
import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_edgeadc_client():
    """Create a mock EdgeADC client."""
    client = Mock()
    client.host = "192.168.1.100"
    client.username = "admin"
    client.guid = "test-guid-12345"
    client.login.return_value = True
    client.create_virtual_service.return_value = (True, {})
    client.delete_virtual_service.return_value = True
    client.add_member.return_value = (True, {})
    client.delete_member.return_value = True
    client.apply_config.return_value = True
    return client


@pytest.fixture
def mock_loadbalancer():
    """Create a mock load balancer."""
    lb = Mock()
    lb.loadbalancer_id = "test-lb-123"
    lb.name = "test-loadbalancer"
    lb.vip_address = "10.0.0.100"
    lb.vip_port_id = "port-123"
    lb.vip_subnet_id = "subnet-123"
    return lb


@pytest.fixture
def mock_listener():
    """Create a mock listener."""
    listener = Mock()
    listener.listener_id = "test-listener-123"
    listener.loadbalancer_id = "test-lb-123"
    listener.name = "test-listener"
    listener.protocol = "HTTP"
    listener.protocol_port = 80
    listener.default_pool_id = "pool-123"
    return listener


@pytest.fixture
def mock_pool():
    """Create a mock pool."""
    pool = Mock()
    pool.pool_id = "test-pool-123"
    pool.name = "test-pool"
    pool.protocol = "HTTP"
    pool.lb_algorithm = "ROUND_ROBIN"
    pool.listener_id = "listener-123"
    return pool


@pytest.fixture
def mock_member():
    """Create a mock member."""
    member = Mock()
    member.member_id = "test-member-123"
    member.pool_id = "pool-123"
    member.address = "10.0.0.10"
    member.protocol_port = 8080
    member.weight = 100
    member.name = "test-member"
    return member


@pytest.fixture
def mock_healthmonitor():
    """Create a mock health monitor."""
    hm = Mock()
    hm.healthmonitor_id = "test-hm-123"
    hm.pool_id = "pool-123"
    hm.type = "HTTP"
    hm.delay = 5
    hm.timeout = 3
    hm.max_retries = 3
    hm.http_method = "GET"
    hm.url_path = "/health"
    hm.expected_codes = "200"
    return hm


@pytest.fixture
def mock_conf():
    """Create mock configuration."""
    with patch('octavia_edgeadc_driver.driver.CONF') as conf:
        conf.edgeadc.edgeadc_host = "192.168.1.100"
        conf.edgeadc.edgeadc_username = "admin"
        conf.edgeadc.edgeadc_password = "password"
        conf.edgeadc.edgeadc_port = 443
        conf.edgeadc.edgeadc_verify_ssl = False
        conf.edgeadc.edgeadc_request_timeout = 30
        conf.edgeadc.edgeadc_default_subnet_mask = "255.255.255.0"
        yield conf
