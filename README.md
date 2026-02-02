<div align="center">

# 🔷 EdgeADC Octavia Driver

**OpenStack Octavia Provider Driver for EdgeNexus EdgeADC**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![OpenStack](https://img.shields.io/badge/OpenStack-Octavia-red.svg)](https://docs.openstack.org/octavia/latest/)
[![CI](https://github.com/edgeNEXUS/Edgeadc_Octavia_Driver/actions/workflows/ci.yml/badge.svg)](https://github.com/edgeNEXUS/Edgeadc_Octavia_Driver/actions)

<img src="https://www.edgenexus.io/wp-content/uploads/2023/03/EdgeNexus-Logo.svg" alt="EdgeNexus Logo" width="300"/>

*Enterprise-grade load balancing for OpenStack clouds*

[Installation](#installation) • [Configuration](#configuration) • [Usage](#usage) • [API Reference](#api-reference) • [Contributing](#contributing)

</div>

---

## 📋 Overview

The **EdgeADC Octavia Driver** enables seamless integration between OpenStack Octavia (Load Balancer as a Service) and EdgeNexus EdgeADC appliances. This driver allows OpenStack users to provision and manage enterprise-grade load balancers through the standard Octavia API.

### Key Features

- ✅ **Full Octavia Integration** - Works with standard OpenStack CLI and Horizon dashboard
- ✅ **High Performance** - Leverages EdgeADC's hardware-accelerated load balancing
- ✅ **SSL Offloading** - Terminate SSL/TLS at the load balancer
- ✅ **Health Monitoring** - Comprehensive health checks for backend servers
- ✅ **Multiple Protocols** - HTTP, HTTPS, TCP, UDP support
- ✅ **Load Balancing Algorithms** - Round Robin, Least Connections, Source IP

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     OpenStack Cloud                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Horizon   │    │  OpenStack  │    │    Octavia API      │  │
│  │  Dashboard  │───▶│     CLI     │───▶│    Controller       │  │
│  └─────────────┘    └─────────────┘    └──────────┬──────────┘  │
│                                                    │             │
│                                         ┌──────────▼──────────┐  │
│                                         │  EdgeADC Octavia    │  │
│                                         │  Provider Driver    │  │
│                                         └──────────┬──────────┘  │
└────────────────────────────────────────────────────┼─────────────┘
                                                     │ REST API
                                          ┌──────────▼──────────┐
                                          │   EdgeNexus EdgeADC │
                                          │      Appliance      │
                                          │  ┌───────────────┐  │
                                          │  │ Virtual IPs   │  │
                                          │  │ Health Checks │  │
                                          │  │ SSL Offload   │  │
                                          │  └───────────────┘  │
                                          └─────────────────────┘
```

### Resource Mapping

| Octavia Resource | EdgeADC Resource |
|------------------|------------------|
| Load Balancer | Device/VIP Container |
| Listener | Virtual Service (VIP) |
| Pool | Load Balancing Configuration |
| Member | Content Server |
| Health Monitor | Monitoring Policy |

---

## 🚀 Installation

### Prerequisites

- OpenStack Octavia (Yoga release or later)
- EdgeNexus EdgeADC appliance (v5.0+)
- Python 3.9+
- Network connectivity between Octavia controller and EdgeADC

### Install from PyPI

```bash
pip install octavia-edgeadc-driver
```

### Install from Source

```bash
git clone https://github.com/edgeNEXUS/Edgeadc_Octavia_Driver.git
cd Edgeadc_Octavia_Driver
pip install -e .
```

### Install on Octavia Controller

```bash
# On your Octavia API/Controller node
sudo pip install octavia-edgeadc-driver

# Restart Octavia services
sudo systemctl restart octavia-api octavia-worker octavia-driver-agent
```

---

## ⚙️ Configuration

### 1. Configure Octavia

Add the EdgeADC driver to `/etc/octavia/octavia.conf`:

```ini
[api_settings]
# Add edgeadc to enabled providers
enabled_provider_drivers = amphora:Amphora,edgeadc:EdgeADC

# Set as default provider (optional)
default_provider_driver = edgeadc

[driver_agent]
# Enable the EdgeADC provider agent
enabled_provider_agents = edgeadc_agent

[edgeadc]
# EdgeADC appliance connection settings
edgeadc_host = 192.168.1.100
edgeadc_username = admin
edgeadc_password = your_secure_password
edgeadc_port = 443
edgeadc_verify_ssl = false
edgeadc_request_timeout = 30
edgeadc_default_subnet_mask = 255.255.255.0
```

### 2. Configure EdgeADC

Ensure your EdgeADC appliance is configured:

1. **Enable REST API** - The REST API is enabled by default on port 443
2. **Create API User** - Create a dedicated user for Octavia with admin privileges
3. **Network Access** - Ensure the Octavia controller can reach EdgeADC on port 443

### 3. Restart Services

```bash
sudo systemctl restart octavia-api
sudo systemctl restart octavia-worker
sudo systemctl restart octavia-driver-agent
```

---

## 📖 Usage

### Using OpenStack CLI

#### Create a Load Balancer

```bash
# Create load balancer using EdgeADC provider
openstack loadbalancer create \
  --name my-lb \
  --provider edgeadc \
  --vip-subnet-id <subnet-id>

# Wait for ACTIVE status
openstack loadbalancer show my-lb
```

#### Create a Listener

```bash
# Create HTTP listener on port 80
openstack loadbalancer listener create \
  --name http-listener \
  --protocol HTTP \
  --protocol-port 80 \
  my-lb
```

#### Create a Pool

```bash
# Create pool with round-robin algorithm
openstack loadbalancer pool create \
  --name web-pool \
  --protocol HTTP \
  --lb-algorithm ROUND_ROBIN \
  --listener http-listener
```

#### Add Members

```bash
# Add backend servers
openstack loadbalancer member create \
  --name web-server-1 \
  --address 10.0.0.10 \
  --protocol-port 8080 \
  web-pool

openstack loadbalancer member create \
  --name web-server-2 \
  --address 10.0.0.11 \
  --protocol-port 8080 \
  web-pool
```

#### Create Health Monitor

```bash
# Create HTTP health check
openstack loadbalancer healthmonitor create \
  --name http-monitor \
  --type HTTP \
  --delay 5 \
  --timeout 3 \
  --max-retries 3 \
  --url-path /health \
  web-pool
```

### Using Horizon Dashboard

1. Navigate to **Project → Network → Load Balancers**
2. Click **Create Load Balancer**
3. Select **edgeadc** as the Provider
4. Follow the wizard to configure listeners, pools, and members

### Complete Example: Web Application

```bash
#!/bin/bash
# Deploy a complete load balancer for a web application

# Variables
SUBNET_ID="your-subnet-id"
LB_NAME="webapp-lb"

# Create load balancer
openstack loadbalancer create \
  --name $LB_NAME \
  --provider edgeadc \
  --vip-subnet-id $SUBNET_ID \
  --wait

# Create HTTPS listener with SSL termination
openstack loadbalancer listener create \
  --name https-listener \
  --protocol TERMINATED_HTTPS \
  --protocol-port 443 \
  --default-tls-container-ref <barbican-secret-ref> \
  $LB_NAME

# Create pool
openstack loadbalancer pool create \
  --name webapp-pool \
  --protocol HTTP \
  --lb-algorithm LEAST_CONNECTIONS \
  --listener https-listener

# Add members
for i in 1 2 3; do
  openstack loadbalancer member create \
    --name webapp-server-$i \
    --address 10.0.0.1$i \
    --protocol-port 8080 \
    --weight 100 \
    webapp-pool
done

# Create health monitor
openstack loadbalancer healthmonitor create \
  --name webapp-monitor \
  --type HTTP \
  --delay 10 \
  --timeout 5 \
  --max-retries 3 \
  --http-method GET \
  --url-path /api/health \
  --expected-codes 200 \
  webapp-pool

# Show final configuration
openstack loadbalancer show $LB_NAME
openstack loadbalancer status show $LB_NAME
```

---

## 🔧 API Reference

### Supported Octavia Features

| Feature | Status | Notes |
|---------|--------|-------|
| Load Balancer CRUD | ✅ Supported | Full lifecycle management |
| Listener CRUD | ✅ Supported | HTTP, HTTPS, TCP, UDP |
| Pool CRUD | ✅ Supported | All algorithms |
| Member CRUD | ✅ Supported | Weight support |
| Health Monitor CRUD | ✅ Supported | HTTP, HTTPS, TCP, PING |
| L7 Policies | 🚧 Planned | Coming in v2.0 |
| L7 Rules | 🚧 Planned | Coming in v2.0 |
| Flavors | ✅ Supported | Custom EdgeADC options |
| Availability Zones | ✅ Supported | Cluster selection |

### Protocol Support

| Octavia Protocol | EdgeADC Service Type |
|------------------|---------------------|
| HTTP | HTTP |
| HTTPS | HTTPS |
| TCP | TCP |
| UDP | UDP |
| TERMINATED_HTTPS | HTTPS (with SSL offload) |
| PROXY | TCP |
| PROXYV2 | TCP |

### Load Balancing Algorithms

| Octavia Algorithm | EdgeADC Algorithm |
|-------------------|-------------------|
| ROUND_ROBIN | RoundRobin |
| LEAST_CONNECTIONS | LeastConnections |
| SOURCE_IP | SourceIP |
| SOURCE_IP_PORT | SourceIP |

---

## 🧪 Testing

### Run Unit Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=octavia_edgeadc_driver --cov-report=html
```

### Integration Testing

```bash
# Set environment variables
export EDGEADC_HOST=192.168.1.100
export EDGEADC_USERNAME=admin
export EDGEADC_PASSWORD=your_password

# Run integration tests
pytest tests/integration/ -v --integration
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/edgeNEXUS/Edgeadc_Octavia_Driver.git
cd Edgeadc_Octavia_Driver

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev,test]"

# Run linting
ruff check .
mypy octavia_edgeadc_driver/

# Run tests
pytest tests/ -v
```

---

## 📄 License

This software is proprietary and confidential. See your license agreement with EdgeNexus for terms of use.

---

## 🔗 Links

- **EdgeNexus Website**: [https://www.edgenexus.io](https://www.edgenexus.io)
- **EdgeADC Documentation**: [https://www.edgenexus.io/support/](https://www.edgenexus.io/support/)
- **OpenStack Octavia**: [https://docs.openstack.org/octavia/latest/](https://docs.openstack.org/octavia/latest/)
- **Issue Tracker**: [GitHub Issues](https://github.com/edgeNEXUS/Edgeadc_Octavia_Driver/issues)

---

<div align="center">

**Made with ❤️ by [EdgeNexus](https://www.edgenexus.io)**

*Enterprise Load Balancing for the Modern Cloud*

</div>
