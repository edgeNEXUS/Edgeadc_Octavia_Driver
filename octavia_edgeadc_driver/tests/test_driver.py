"""
Unit tests for EdgeADC Octavia provider driver.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from octavia_edgeadc_driver.common import constants


class TestEdgeADCProviderDriver:
    """Tests for EdgeADCProviderDriver class."""

    @patch('octavia_edgeadc_driver.driver.driver_lib.DriverLibrary')
    @patch('octavia_edgeadc_driver.driver.driver_config.register_opts')
    def setup_method(self, method, mock_register, mock_driver_lib):
        """Set up test fixtures."""
        mock_driver_lib.return_value = Mock()
        
        from octavia_edgeadc_driver.driver import EdgeADCProviderDriver
        self.driver = EdgeADCProviderDriver()
        self.driver.driver_lib = Mock()

    def test_driver_initialization(self):
        """Test driver initializes correctly."""
        assert self.driver is not None
        assert hasattr(self.driver, 'driver_lib')
        assert hasattr(self.driver, '_clients')

    @patch('octavia_edgeadc_driver.driver.EdgeADCClient')
    def test_get_client(self, mock_client_class):
        """Test getting EdgeADC client."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        with patch('octavia_edgeadc_driver.driver.CONF') as mock_conf:
            mock_conf.edgeadc.edgeadc_host = "192.168.1.100"
            mock_conf.edgeadc.edgeadc_username = "admin"
            mock_conf.edgeadc.edgeadc_password = "password"
            mock_conf.edgeadc.edgeadc_port = 443
            mock_conf.edgeadc.edgeadc_request_timeout = 30
            mock_conf.edgeadc.edgeadc_verify_ssl = False
            
            client = self.driver._get_client()
            
        assert client is not None

    def test_update_status(self):
        """Test status update."""
        status_dict = {
            "loadbalancers": [{
                "id": "test-lb-id",
                "provisioning_status": constants.PROVISIONING_STATUS_ACTIVE
            }]
        }
        
        self.driver._update_status(status_dict)
        self.driver.driver_lib.update_loadbalancer_status.assert_called_once_with(status_dict)


class TestLoadBalancerOperations:
    """Tests for load balancer operations."""

    @patch('octavia_edgeadc_driver.driver.driver_lib.DriverLibrary')
    @patch('octavia_edgeadc_driver.driver.driver_config.register_opts')
    def setup_method(self, method, mock_register, mock_driver_lib):
        """Set up test fixtures."""
        mock_driver_lib.return_value = Mock()
        
        from octavia_edgeadc_driver.driver import EdgeADCProviderDriver
        self.driver = EdgeADCProviderDriver()
        self.driver.driver_lib = Mock()

    @patch('octavia_edgeadc_driver.driver.EdgeADCClient')
    def test_loadbalancer_create_success(self, mock_client_class):
        """Test successful load balancer creation."""
        mock_client = Mock()
        mock_client.login.return_value = True
        mock_client_class.return_value = mock_client
        
        lb = Mock()
        lb.loadbalancer_id = "test-lb-123"
        
        with patch('octavia_edgeadc_driver.driver.CONF') as mock_conf:
            mock_conf.edgeadc.edgeadc_host = "192.168.1.100"
            mock_conf.edgeadc.edgeadc_username = "admin"
            mock_conf.edgeadc.edgeadc_password = "password"
            mock_conf.edgeadc.edgeadc_port = 443
            mock_conf.edgeadc.edgeadc_request_timeout = 30
            mock_conf.edgeadc.edgeadc_verify_ssl = False
            
            self.driver.loadbalancer_create(lb)
        
        self.driver.driver_lib.update_loadbalancer_status.assert_called()

    def test_loadbalancer_delete(self):
        """Test load balancer deletion."""
        lb = Mock()
        lb.loadbalancer_id = "test-lb-123"
        
        self.driver.loadbalancer_delete(lb)
        
        self.driver.driver_lib.update_loadbalancer_status.assert_called()

    def test_loadbalancer_failover(self):
        """Test load balancer failover."""
        self.driver.loadbalancer_failover("test-lb-123")
        
        self.driver.driver_lib.update_loadbalancer_status.assert_called()


class TestListenerOperations:
    """Tests for listener operations."""

    @patch('octavia_edgeadc_driver.driver.driver_lib.DriverLibrary')
    @patch('octavia_edgeadc_driver.driver.driver_config.register_opts')
    def setup_method(self, method, mock_register, mock_driver_lib):
        """Set up test fixtures."""
        mock_driver_lib.return_value = Mock()
        
        from octavia_edgeadc_driver.driver import EdgeADCProviderDriver
        self.driver = EdgeADCProviderDriver()
        self.driver.driver_lib = Mock()

    @patch('octavia_edgeadc_driver.driver.EdgeADCClient')
    def test_listener_create(self, mock_client_class):
        """Test listener creation."""
        mock_client = Mock()
        mock_client.create_virtual_service.return_value = (True, {})
        mock_client_class.return_value = mock_client
        
        listener = Mock()
        listener.listener_id = "test-listener-123"
        listener.loadbalancer_id = "test-lb-123"
        listener.protocol = "HTTP"
        listener.protocol_port = 80
        listener.name = "test-listener"
        
        with patch('octavia_edgeadc_driver.driver.CONF') as mock_conf:
            mock_conf.edgeadc.edgeadc_host = "192.168.1.100"
            mock_conf.edgeadc.edgeadc_username = "admin"
            mock_conf.edgeadc.edgeadc_password = "password"
            mock_conf.edgeadc.edgeadc_port = 443
            mock_conf.edgeadc.edgeadc_request_timeout = 30
            mock_conf.edgeadc.edgeadc_verify_ssl = False
            mock_conf.edgeadc.edgeadc_default_subnet_mask = "255.255.255.0"
            
            self.driver.listener_create(listener)
        
        self.driver.driver_lib.update_loadbalancer_status.assert_called()


class TestPoolOperations:
    """Tests for pool operations."""

    @patch('octavia_edgeadc_driver.driver.driver_lib.DriverLibrary')
    @patch('octavia_edgeadc_driver.driver.driver_config.register_opts')
    def setup_method(self, method, mock_register, mock_driver_lib):
        """Set up test fixtures."""
        mock_driver_lib.return_value = Mock()
        
        from octavia_edgeadc_driver.driver import EdgeADCProviderDriver
        self.driver = EdgeADCProviderDriver()
        self.driver.driver_lib = Mock()

    def test_pool_create(self):
        """Test pool creation."""
        pool = Mock()
        pool.pool_id = "test-pool-123"
        
        self.driver.pool_create(pool)
        
        self.driver.driver_lib.update_loadbalancer_status.assert_called()

    def test_pool_delete(self):
        """Test pool deletion."""
        pool = Mock()
        pool.pool_id = "test-pool-123"
        
        self.driver.pool_delete(pool)
        
        self.driver.driver_lib.update_loadbalancer_status.assert_called()


class TestMemberOperations:
    """Tests for member operations."""

    @patch('octavia_edgeadc_driver.driver.driver_lib.DriverLibrary')
    @patch('octavia_edgeadc_driver.driver.driver_config.register_opts')
    def setup_method(self, method, mock_register, mock_driver_lib):
        """Set up test fixtures."""
        mock_driver_lib.return_value = Mock()
        
        from octavia_edgeadc_driver.driver import EdgeADCProviderDriver
        self.driver = EdgeADCProviderDriver()
        self.driver.driver_lib = Mock()

    @patch('octavia_edgeadc_driver.driver.EdgeADCClient')
    def test_member_create(self, mock_client_class):
        """Test member creation."""
        mock_client = Mock()
        mock_client.add_member.return_value = (True, {})
        mock_client_class.return_value = mock_client
        
        member = Mock()
        member.member_id = "test-member-123"
        member.address = "10.0.0.10"
        member.protocol_port = 8080
        member.weight = 100
        
        with patch('octavia_edgeadc_driver.driver.CONF') as mock_conf:
            mock_conf.edgeadc.edgeadc_host = "192.168.1.100"
            mock_conf.edgeadc.edgeadc_username = "admin"
            mock_conf.edgeadc.edgeadc_password = "password"
            mock_conf.edgeadc.edgeadc_port = 443
            mock_conf.edgeadc.edgeadc_request_timeout = 30
            mock_conf.edgeadc.edgeadc_verify_ssl = False
            
            self.driver.member_create(member)
        
        self.driver.driver_lib.update_loadbalancer_status.assert_called()


class TestHealthMonitorOperations:
    """Tests for health monitor operations."""

    @patch('octavia_edgeadc_driver.driver.driver_lib.DriverLibrary')
    @patch('octavia_edgeadc_driver.driver.driver_config.register_opts')
    def setup_method(self, method, mock_register, mock_driver_lib):
        """Set up test fixtures."""
        mock_driver_lib.return_value = Mock()
        
        from octavia_edgeadc_driver.driver import EdgeADCProviderDriver
        self.driver = EdgeADCProviderDriver()
        self.driver.driver_lib = Mock()

    def test_health_monitor_create(self):
        """Test health monitor creation."""
        hm = Mock()
        hm.healthmonitor_id = "test-hm-123"
        
        self.driver.health_monitor_create(hm)
        
        self.driver.driver_lib.update_loadbalancer_status.assert_called()


class TestFlavorSupport:
    """Tests for flavor support."""

    @patch('octavia_edgeadc_driver.driver.driver_lib.DriverLibrary')
    @patch('octavia_edgeadc_driver.driver.driver_config.register_opts')
    def setup_method(self, method, mock_register, mock_driver_lib):
        """Set up test fixtures."""
        mock_driver_lib.return_value = Mock()
        
        from octavia_edgeadc_driver.driver import EdgeADCProviderDriver
        self.driver = EdgeADCProviderDriver()

    def test_get_supported_flavor_metadata(self):
        """Test getting supported flavor metadata."""
        metadata = self.driver.get_supported_flavor_metadata()
        
        assert "edgeadc_device" in metadata
        assert "ssl_offload" in metadata
        assert "compression" in metadata

    def test_validate_flavor_valid(self):
        """Test validating valid flavor."""
        self.driver.validate_flavor({"edgeadc_device": "192.168.1.100"})

    def test_validate_flavor_invalid(self):
        """Test validating invalid flavor."""
        from octavia_lib.api.drivers import exceptions as driver_exceptions
        
        with pytest.raises(driver_exceptions.UnsupportedOptionError):
            self.driver.validate_flavor({"invalid_option": "value"})
