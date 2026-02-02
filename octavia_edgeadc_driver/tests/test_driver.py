"""
Unit tests for EdgeADC Octavia driver.

Note: Driver tests require OpenStack dependencies (oslo_config, octavia_lib).
These tests are skipped in CI when dependencies are not available.
"""
import pytest

# Skip all tests in this module if oslo_config is not available
pytest.importorskip("oslo_config", reason="oslo_config not installed")

from unittest.mock import Mock, patch


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


class TestEdgeADCProviderDriver:
    """Tests for EdgeADC provider driver."""

    @patch('octavia_edgeadc_driver.driver.CONF')
    def test_driver_initialization(self, mock_conf):
        """Test driver initialization."""
        mock_conf.edgeadc.edgeadc_host = "192.168.1.100"
        mock_conf.edgeadc.edgeadc_username = "admin"
        mock_conf.edgeadc.edgeadc_password = "password"
        mock_conf.edgeadc.edgeadc_port = 443
        mock_conf.edgeadc.edgeadc_verify_ssl = False
        mock_conf.edgeadc.edgeadc_request_timeout = 30
        mock_conf.edgeadc.edgeadc_default_subnet_mask = "255.255.255.0"

        from octavia_edgeadc_driver.driver import EdgeADCProviderDriver
        driver = EdgeADCProviderDriver()
        assert driver is not None
