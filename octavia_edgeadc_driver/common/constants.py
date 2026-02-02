"""
Constants for the EdgeADC Octavia driver.
"""

# Driver name
DRIVER_NAME = 'edgeadc'

# EdgeADC API endpoints
API_LOGIN = '/POST/32'
API_IP_SERVICES = '/GET/9'
API_SYSTEM_INFO = '/GET/5'
API_CLUSTER_STATUS = '/GET/30'

# VIP operations (Terraform-style two-step approach)
API_VIP_CREATE_TEMPLATE = '/POST/9?iAction=3&iType=1&FilterKeyword='
API_VIP_UPDATE_TEMPLATE = '/POST/9?iAction=2&iType=1&FilterKeyword='
API_VIP_DELETE = '/POST/9?iAction=3&iType=4&FilterKeyword='
API_SERVER_ADD_INIT = '/POST/9?iAction=3&iType=3&FilterKeyword='
API_SERVER_ADD_UPDATE = '/POST/9?iAction=2&iType=2&FilterKeyword='
API_SERVER_DELETE = '/POST/9?iAction=3&iType=5&FilterKeyword='
API_APPLY_CONFIG = '/POST/5?iAction=1'

# Protocol mappings: Octavia -> EdgeADC
PROTOCOL_MAP = {
    'HTTP': 'HTTP',
    'HTTPS': 'HTTPS',
    'TCP': 'TCP',
    'UDP': 'UDP',
    'TERMINATED_HTTPS': 'HTTPS',
    'PROXY': 'TCP',
    'PROXYV2': 'TCP',
}

# Load balancing algorithm mappings: Octavia -> EdgeADC
LB_ALGORITHM_MAP = {
    'ROUND_ROBIN': 'RoundRobin',
    'LEAST_CONNECTIONS': 'LeastConnections',
    'SOURCE_IP': 'SourceIP',
    'SOURCE_IP_PORT': 'SourceIP',
}

# Health monitor type mappings: Octavia -> EdgeADC
HEALTH_MONITOR_MAP = {
    'HTTP': 'HTTP',
    'HTTPS': 'HTTPS',
    'TCP': 'TCP',
    'PING': 'ICMP',
    'TLS-HELLO': 'TCP',
    'UDP-CONNECT': 'UDP',
    'SCTP': 'TCP',
}

# Operating status values
OPERATING_STATUS_ONLINE = 'ONLINE'
OPERATING_STATUS_OFFLINE = 'OFFLINE'
OPERATING_STATUS_DEGRADED = 'DEGRADED'
OPERATING_STATUS_ERROR = 'ERROR'
OPERATING_STATUS_NO_MONITOR = 'NO_MONITOR'

# Provisioning status values
PROVISIONING_STATUS_ACTIVE = 'ACTIVE'
PROVISIONING_STATUS_DELETED = 'DELETED'
PROVISIONING_STATUS_ERROR = 'ERROR'
PROVISIONING_STATUS_PENDING_CREATE = 'PENDING_CREATE'
PROVISIONING_STATUS_PENDING_UPDATE = 'PENDING_UPDATE'
PROVISIONING_STATUS_PENDING_DELETE = 'PENDING_DELETE'
