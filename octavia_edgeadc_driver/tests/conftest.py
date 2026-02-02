"""
Pytest configuration and fixtures for EdgeADC driver tests.
"""
import pytest
from unittest.mock import Mock


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
