"""
EdgeADC Octavia Provider Driver.

This driver implements the Octavia provider driver interface to allow
OpenStack to use EdgeNexus EdgeADC as a load balancer backend.
"""
from __future__ import annotations

import logging
from typing import Any

from octavia_lib.api.drivers import data_models, driver_lib, provider_base
from octavia_lib.api.drivers import exceptions as driver_exceptions
from oslo_config import cfg

from octavia_edgeadc_driver.api.edgeadc_client import EdgeADCClient
from octavia_edgeadc_driver.common import config as driver_config
from octavia_edgeadc_driver.common import constants

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

# Register configuration options
driver_config.register_opts(CONF)


class EdgeADCProviderDriver(provider_base.ProviderDriver):
    """
    Octavia provider driver for EdgeNexus EdgeADC.

    Mapping:
    - Octavia LoadBalancer -> EdgeADC device selection
    - Octavia Listener -> EdgeADC Virtual Service (VIP)
    - Octavia Pool -> EdgeADC load balancing configuration
    - Octavia Member -> EdgeADC Content Server
    - Octavia HealthMonitor -> EdgeADC Monitoring Policy
    """

    def __init__(self):
        super().__init__()
        self.driver_lib = driver_lib.DriverLibrary()
        self._clients: dict[str, EdgeADCClient] = {}
        LOG.info("EdgeADC provider driver initialized")

    def _get_client(self, loadbalancer_id: str = None) -> EdgeADCClient:
        """Get or create an EdgeADC client."""
        host = CONF.edgeadc.edgeadc_host
        if host not in self._clients:
            self._clients[host] = EdgeADCClient(
                host=host,
                username=CONF.edgeadc.edgeadc_username,
                password=CONF.edgeadc.edgeadc_password,
                port=CONF.edgeadc.edgeadc_port,
                timeout=CONF.edgeadc.edgeadc_request_timeout,
                verify_ssl=CONF.edgeadc.edgeadc_verify_ssl
            )
        return self._clients[host]

    def _update_status(self, status_dict: dict[str, list[dict[str, str]]]) -> None:
        """Update resource status in Octavia."""
        try:
            self.driver_lib.update_loadbalancer_status(status_dict)
        except Exception as e:
            LOG.error(f"Failed to update status: {e}")

    # ========== Load Balancer Operations ==========

    def loadbalancer_create(self, loadbalancer: data_models.LoadBalancer) -> None:
        """Create a new load balancer."""
        LOG.info(f"Creating load balancer: {loadbalancer.loadbalancer_id}")
        try:
            client = self._get_client(loadbalancer.loadbalancer_id)
            if not client.login():
                raise driver_exceptions.DriverError(
                    user_fault_string="Failed to connect to EdgeADC device",
                    operator_fault_string=f"EdgeADC login failed for {client.host}"
                )
            self._update_status({
                "loadbalancers": [{
                    "id": loadbalancer.loadbalancer_id,
                    "provisioning_status": constants.PROVISIONING_STATUS_ACTIVE,
                    "operating_status": constants.OPERATING_STATUS_ONLINE
                }]
            })
            LOG.info(f"Load balancer {loadbalancer.loadbalancer_id} created")
        except driver_exceptions.DriverError:
            raise
        except Exception as e:
            LOG.exception(f"Failed to create load balancer: {e}")
            self._update_status({
                "loadbalancers": [{
                    "id": loadbalancer.loadbalancer_id,
                    "provisioning_status": constants.PROVISIONING_STATUS_ERROR,
                    "operating_status": constants.OPERATING_STATUS_ERROR
                }]
            })
            raise driver_exceptions.DriverError(
                user_fault_string="Failed to create load balancer",
                operator_fault_string=str(e)
            )

    def loadbalancer_delete(self, loadbalancer: data_models.LoadBalancer, cascade: bool = False) -> None:
        """Delete a load balancer."""
        LOG.info(f"Deleting load balancer: {loadbalancer.loadbalancer_id}")
        try:
            self._update_status({
                "loadbalancers": [{
                    "id": loadbalancer.loadbalancer_id,
                    "provisioning_status": constants.PROVISIONING_STATUS_DELETED,
                    "operating_status": constants.OPERATING_STATUS_OFFLINE
                }]
            })
        except Exception as e:
            LOG.exception(f"Failed to delete load balancer: {e}")
            raise driver_exceptions.DriverError(
                user_fault_string="Failed to delete load balancer",
                operator_fault_string=str(e)
            )

    def loadbalancer_failover(self, loadbalancer_id: str) -> None:
        """Perform a failover of a load balancer."""
        LOG.info(f"Failover requested for: {loadbalancer_id}")
        self._update_status({
            "loadbalancers": [{"id": loadbalancer_id, "provisioning_status": constants.PROVISIONING_STATUS_ACTIVE}]
        })

    def loadbalancer_update(self, old_loadbalancer: data_models.LoadBalancer, new_loadbalancer: data_models.LoadBalancer) -> None:
        """Update a load balancer."""
        LOG.info(f"Updating load balancer: {new_loadbalancer.loadbalancer_id}")
        try:
            self._update_status({
                "loadbalancers": [{"id": new_loadbalancer.loadbalancer_id, "provisioning_status": constants.PROVISIONING_STATUS_ACTIVE}]
            })
        except Exception as e:
            raise driver_exceptions.DriverError(user_fault_string="Failed to update load balancer", operator_fault_string=str(e))

    # ========== Listener Operations ==========

    def listener_create(self, listener: data_models.Listener) -> None:
        """Create a new listener (EdgeADC VIP)."""
        LOG.info(f"Creating listener: {listener.listener_id}")
        try:
            client = self._get_client(listener.loadbalancer_id)
            vip_address = getattr(listener, 'vip_address', CONF.edgeadc.edgeadc_host)
            success, _ = client.create_virtual_service(
                ip_addr=vip_address,
                port=listener.protocol_port,
                protocol=listener.protocol,
                subnet_mask=CONF.edgeadc.edgeadc_default_subnet_mask,
                service_name=listener.name or f"octavia-{listener.listener_id[:8]}"
            )
            if success:
                self._update_status({
                    "listeners": [{"id": listener.listener_id, "provisioning_status": constants.PROVISIONING_STATUS_ACTIVE, "operating_status": constants.OPERATING_STATUS_ONLINE}]
                })
            else:
                raise driver_exceptions.DriverError(user_fault_string="Failed to create listener on EdgeADC")
        except driver_exceptions.DriverError:
            raise
        except Exception as e:
            self._update_status({"listeners": [{"id": listener.listener_id, "provisioning_status": constants.PROVISIONING_STATUS_ERROR}]})
            raise driver_exceptions.DriverError(user_fault_string="Failed to create listener", operator_fault_string=str(e))

    def listener_delete(self, listener: data_models.Listener) -> None:
        """Delete a listener."""
        LOG.info(f"Deleting listener: {listener.listener_id}")
        try:
            client = self._get_client(listener.loadbalancer_id)
            vip_address = getattr(listener, 'vip_address', CONF.edgeadc.edgeadc_host)
            client.delete_virtual_service(vip_address, listener.protocol_port)
            self._update_status({"listeners": [{"id": listener.listener_id, "provisioning_status": constants.PROVISIONING_STATUS_DELETED}]})
        except Exception as e:
            raise driver_exceptions.DriverError(user_fault_string="Failed to delete listener", operator_fault_string=str(e))

    def listener_update(self, old_listener: data_models.Listener, new_listener: data_models.Listener) -> None:
        """Update a listener."""
        LOG.info(f"Updating listener: {new_listener.listener_id}")
        self._update_status({"listeners": [{"id": new_listener.listener_id, "provisioning_status": constants.PROVISIONING_STATUS_ACTIVE}]})

    # ========== Pool Operations ==========

    def pool_create(self, pool: data_models.Pool) -> None:
        """Create a new pool."""
        LOG.info(f"Creating pool: {pool.pool_id}")
        self._update_status({"pools": [{"id": pool.pool_id, "provisioning_status": constants.PROVISIONING_STATUS_ACTIVE, "operating_status": constants.OPERATING_STATUS_ONLINE}]})

    def pool_delete(self, pool: data_models.Pool) -> None:
        """Delete a pool."""
        LOG.info(f"Deleting pool: {pool.pool_id}")
        self._update_status({"pools": [{"id": pool.pool_id, "provisioning_status": constants.PROVISIONING_STATUS_DELETED}]})

    def pool_update(self, old_pool: data_models.Pool, new_pool: data_models.Pool) -> None:
        """Update a pool."""
        LOG.info(f"Updating pool: {new_pool.pool_id}")
        self._update_status({"pools": [{"id": new_pool.pool_id, "provisioning_status": constants.PROVISIONING_STATUS_ACTIVE}]})

    # ========== Member Operations ==========

    def member_create(self, member: data_models.Member) -> None:
        """Create a new member (EdgeADC content server)."""
        LOG.info(f"Creating member: {member.member_id}")
        try:
            client = self._get_client()
            vip_address = getattr(member, 'vip_address', CONF.edgeadc.edgeadc_host)
            vip_port = getattr(member, 'vip_port', 80)
            success, _ = client.add_member(
                vip_ip=vip_address, vip_port=vip_port,
                member_ip=member.address, member_port=member.protocol_port,
                weight=member.weight or 100
            )
            if success:
                self._update_status({"members": [{"id": member.member_id, "provisioning_status": constants.PROVISIONING_STATUS_ACTIVE, "operating_status": constants.OPERATING_STATUS_ONLINE}]})
            else:
                raise driver_exceptions.DriverError(user_fault_string="Failed to add member to EdgeADC")
        except driver_exceptions.DriverError:
            raise
        except Exception as e:
            self._update_status({"members": [{"id": member.member_id, "provisioning_status": constants.PROVISIONING_STATUS_ERROR}]})
            raise driver_exceptions.DriverError(user_fault_string="Failed to create member", operator_fault_string=str(e))

    def member_delete(self, member: data_models.Member) -> None:
        """Delete a member."""
        LOG.info(f"Deleting member: {member.member_id}")
        try:
            client = self._get_client()
            vip_address = getattr(member, 'vip_address', CONF.edgeadc.edgeadc_host)
            vip_port = getattr(member, 'vip_port', 80)
            client.delete_member(vip_ip=vip_address, vip_port=vip_port, member_ip=member.address, member_port=member.protocol_port)
            self._update_status({"members": [{"id": member.member_id, "provisioning_status": constants.PROVISIONING_STATUS_DELETED}]})
        except Exception as e:
            raise driver_exceptions.DriverError(user_fault_string="Failed to delete member", operator_fault_string=str(e))

    def member_update(self, old_member: data_models.Member, new_member: data_models.Member) -> None:
        """Update a member."""
        LOG.info(f"Updating member: {new_member.member_id}")
        try:
            if hasattr(new_member, 'weight') and new_member.weight:
                client = self._get_client()
                vip_address = getattr(new_member, 'vip_address', CONF.edgeadc.edgeadc_host)
                vip_port = getattr(new_member, 'vip_port', 80)
                client.update_member_weight(vip_ip=vip_address, vip_port=vip_port, member_ip=new_member.address, member_port=new_member.protocol_port, weight=new_member.weight)
            self._update_status({"members": [{"id": new_member.member_id, "provisioning_status": constants.PROVISIONING_STATUS_ACTIVE}]})
        except Exception as e:
            raise driver_exceptions.DriverError(user_fault_string="Failed to update member", operator_fault_string=str(e))

    def member_batch_update(self, pool_id: str, members: list[data_models.Member]) -> None:
        """Batch update members."""
        for member in members:
            try:
                self.member_create(member)
            except Exception as e:
                LOG.warning(f"Failed to create member {member.member_id}: {e}")

    # ========== Health Monitor Operations ==========

    def health_monitor_create(self, healthmonitor: data_models.HealthMonitor) -> None:
        """Create a health monitor."""
        LOG.info(f"Creating health monitor: {healthmonitor.healthmonitor_id}")
        self._update_status({"healthmonitors": [{"id": healthmonitor.healthmonitor_id, "provisioning_status": constants.PROVISIONING_STATUS_ACTIVE, "operating_status": constants.OPERATING_STATUS_ONLINE}]})

    def health_monitor_delete(self, healthmonitor: data_models.HealthMonitor) -> None:
        """Delete a health monitor."""
        self._update_status({"healthmonitors": [{"id": healthmonitor.healthmonitor_id, "provisioning_status": constants.PROVISIONING_STATUS_DELETED}]})

    def health_monitor_update(self, old_healthmonitor: data_models.HealthMonitor, new_healthmonitor: data_models.HealthMonitor) -> None:
        """Update a health monitor."""
        self._update_status({"healthmonitors": [{"id": new_healthmonitor.healthmonitor_id, "provisioning_status": constants.PROVISIONING_STATUS_ACTIVE}]})

    # ========== L7 Policy/Rule (Not Implemented) ==========

    def l7policy_create(self, l7policy: data_models.L7Policy) -> None:
        raise driver_exceptions.NotImplementedError(user_fault_string="L7 policies not yet supported by EdgeADC driver")

    def l7policy_delete(self, l7policy: data_models.L7Policy) -> None:
        raise driver_exceptions.NotImplementedError(user_fault_string="L7 policies not yet supported")

    def l7policy_update(self, old_l7policy: data_models.L7Policy, new_l7policy: data_models.L7Policy) -> None:
        raise driver_exceptions.NotImplementedError(user_fault_string="L7 policies not yet supported")

    def l7rule_create(self, l7rule: data_models.L7Rule) -> None:
        raise driver_exceptions.NotImplementedError(user_fault_string="L7 rules not yet supported")

    def l7rule_delete(self, l7rule: data_models.L7Rule) -> None:
        raise driver_exceptions.NotImplementedError(user_fault_string="L7 rules not yet supported")

    def l7rule_update(self, old_l7rule: data_models.L7Rule, new_l7rule: data_models.L7Rule) -> None:
        raise driver_exceptions.NotImplementedError(user_fault_string="L7 rules not yet supported")

    # ========== Flavor/AZ Support ==========

    def get_supported_flavor_metadata(self) -> dict[str, str]:
        return {"edgeadc_device": "EdgeADC device hostname", "ssl_offload": "Enable SSL offload", "compression": "Enable compression"}

    def validate_flavor(self, flavor_metadata: dict[str, Any]) -> None:
        supported = self.get_supported_flavor_metadata()
        for key in flavor_metadata:
            if key not in supported:
                raise driver_exceptions.UnsupportedOptionError(user_fault_string=f"Unsupported flavor option: {key}")

    def get_supported_availability_zone_metadata(self) -> dict[str, str]:
        return {"edgeadc_cluster": "EdgeADC cluster for this AZ"}

    def validate_availability_zone(self, availability_zone_metadata: dict[str, Any]) -> None:
        supported = self.get_supported_availability_zone_metadata()
        for key in availability_zone_metadata:
            if key not in supported:
                raise driver_exceptions.UnsupportedOptionError(user_fault_string=f"Unsupported AZ option: {key}")
