"""
EdgeADC Provider Agent for Octavia.

This module provides the provider agent entry point for the Octavia driver agent.
"""
import logging

from oslo_config import cfg

from octavia_edgeadc_driver.common import config as driver_config

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def edgeadc_provider_agent():
    """Entry point for the EdgeADC provider agent.

    This function is called by the Octavia driver agent to initialize
    the EdgeADC provider. It registers configuration options and sets
    up any necessary background tasks.
    """
    driver_config.register_opts(CONF)
    LOG.info("EdgeADC provider agent started")

    # The agent runs as part of the Octavia driver agent process
    # No additional background tasks needed for basic operation
    return None
