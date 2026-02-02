"""
Configuration options for the EdgeADC Octavia driver.
"""
from oslo_config import cfg

EDGEADC_OPTS = [
    cfg.StrOpt(
        'edgeadc_host',
        default='',
        help='EdgeADC device hostname or IP address'
    ),
    cfg.StrOpt(
        'edgeadc_username',
        default='admin',
        help='EdgeADC admin username'
    ),
    cfg.StrOpt(
        'edgeadc_password',
        default='',
        secret=True,
        help='EdgeADC admin password'
    ),
    cfg.IntOpt(
        'edgeadc_port',
        default=443,
        help='EdgeADC HTTPS port'
    ),
    cfg.BoolOpt(
        'edgeadc_verify_ssl',
        default=False,
        help='Verify SSL certificates when connecting to EdgeADC'
    ),
    cfg.IntOpt(
        'edgeadc_request_timeout',
        default=30,
        help='Timeout in seconds for EdgeADC API requests'
    ),
    cfg.StrOpt(
        'edgeadc_default_subnet_mask',
        default='255.255.255.0',
        help='Default subnet mask for VIPs'
    ),
]


def register_opts(conf):
    """Register EdgeADC driver configuration options."""
    conf.register_opts(EDGEADC_OPTS, group='edgeadc')


def list_opts():
    """Return a list of oslo.config options for documentation."""
    return [('edgeadc', EDGEADC_OPTS)]
