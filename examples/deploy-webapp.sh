#!/bin/bash
# =============================================================================
# Example: Deploy a complete web application load balancer using EdgeADC
# =============================================================================
#
# This script demonstrates how to create a production-ready load balancer
# configuration using the EdgeADC Octavia driver.
#
# Prerequisites:
# - OpenStack CLI installed and configured
# - EdgeADC Octavia driver installed
# - Valid OpenStack credentials (source your openrc file)
#
# Usage:
#   ./deploy-webapp.sh <subnet-id> [lb-name]
#
# =============================================================================

set -e

# Configuration
SUBNET_ID="${1:?Usage: $0 <subnet-id> [lb-name]}"
LB_NAME="${2:-webapp-lb}"
PROVIDER="edgeadc"

echo "=============================================="
echo "EdgeADC Load Balancer Deployment"
echo "=============================================="
echo "Subnet ID: $SUBNET_ID"
echo "LB Name: $LB_NAME"
echo "Provider: $PROVIDER"
echo "=============================================="

# Step 1: Create Load Balancer
echo ""
echo "[1/5] Creating load balancer..."
openstack loadbalancer create \
    --name "$LB_NAME" \
    --provider "$PROVIDER" \
    --vip-subnet-id "$SUBNET_ID" \
    --wait

LB_VIP=$(openstack loadbalancer show "$LB_NAME" -f value -c vip_address)
echo "Load balancer created with VIP: $LB_VIP"

# Step 2: Create HTTPS Listener
echo ""
echo "[2/5] Creating HTTPS listener..."
openstack loadbalancer listener create \
    --name "${LB_NAME}-https" \
    --protocol HTTPS \
    --protocol-port 443 \
    "$LB_NAME"

# Also create HTTP listener for redirect (optional)
openstack loadbalancer listener create \
    --name "${LB_NAME}-http" \
    --protocol HTTP \
    --protocol-port 80 \
    "$LB_NAME"

echo "Listeners created (HTTP:80, HTTPS:443)"

# Step 3: Create Pool
echo ""
echo "[3/5] Creating backend pool..."
openstack loadbalancer pool create \
    --name "${LB_NAME}-pool" \
    --protocol HTTP \
    --lb-algorithm LEAST_CONNECTIONS \
    --listener "${LB_NAME}-https"

echo "Pool created with LEAST_CONNECTIONS algorithm"

# Step 4: Add Members (example backend servers)
echo ""
echo "[4/5] Adding backend members..."

# Add your backend servers here
# Replace these IPs with your actual backend server IPs
BACKENDS=(
    "10.0.0.10:8080"
    "10.0.0.11:8080"
    "10.0.0.12:8080"
)

for backend in "${BACKENDS[@]}"; do
    IP="${backend%:*}"
    PORT="${backend#*:}"
    
    echo "  Adding member: $IP:$PORT"
    openstack loadbalancer member create \
        --name "backend-${IP}" \
        --address "$IP" \
        --protocol-port "$PORT" \
        --weight 100 \
        "${LB_NAME}-pool" || echo "  Warning: Failed to add $IP:$PORT"
done

echo "Backend members added"

# Step 5: Create Health Monitor
echo ""
echo "[5/5] Creating health monitor..."
openstack loadbalancer healthmonitor create \
    --name "${LB_NAME}-monitor" \
    --type HTTP \
    --delay 10 \
    --timeout 5 \
    --max-retries 3 \
    --http-method GET \
    --url-path /health \
    --expected-codes 200 \
    "${LB_NAME}-pool"

echo "Health monitor created"

# Summary
echo ""
echo "=============================================="
echo "Deployment Complete!"
echo "=============================================="
echo ""
echo "Load Balancer: $LB_NAME"
echo "VIP Address: $LB_VIP"
echo "HTTPS: https://$LB_VIP"
echo "HTTP: http://$LB_VIP"
echo ""
echo "To check status:"
echo "  openstack loadbalancer show $LB_NAME"
echo "  openstack loadbalancer status show $LB_NAME"
echo ""
echo "To list members:"
echo "  openstack loadbalancer member list ${LB_NAME}-pool"
echo ""
