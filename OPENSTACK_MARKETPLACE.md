# OpenStack Marketplace Listing Guide

## Overview

The OpenStack Marketplace (https://www.openstack.org/marketplace/) is the official directory for OpenStack-related products and services. The Drivers section lists compute, storage, and networking drivers that integrate with OpenStack.

## Current Status (Research: 2026-02-02)

1. **Manual Submission Process**: OpenStack Marketplace uses manual submission through the Foundation member portal
2. **No Public API**: No public API for automated marketplace listing submissions  
3. **Member Account Required**: Requires OpenStack Foundation member account

## How to List the EdgeADC Octavia Driver

### Step 1: Create OpenStack Foundation Account
1. Visit https://www.openstack.org/join/
2. Sign up for Foundation Membership (free individual membership available)
3. Complete profile with EdgeNexus company information

### Step 2: Submit Driver Listing
1. Contact marketplace team at [email protected]
2. Provide:
   - **Product Name**: EdgeADC Octavia Driver
   - **Category**: Drivers > Networking
   - **Description**: OpenStack Octavia provider driver for EdgeNexus EdgeADC
   - **Version**: 1.0.0
   - **OpenStack Compatibility**: Yoga release or later
   - **GitHub**: https://github.com/edgeNEXUS/Edgeadc_Octavia_Driver
   - **License**: Proprietary
   - **Installation**: pip install octavia-edgeadc-driver

## Automation Possibilities

### Cannot Be Automated
- Marketplace submission (no API)
- Manual review by OpenStack Foundation
- Company verification
- Logo/branding upload

### Can Be Partially Automated
1. **Documentation Generation** - Extract from README.md
2. **Submission Package** - Create marketplace-submission.json
3. **Notifications** - Email/issue when new release published

### Recommended: Add to Release Workflow

```yaml
- name: Create Marketplace Update Issue
  run: |
    echo "New release published - update OpenStack Marketplace listing"
    echo "Version: ${{ github.ref_name }}"
    echo "Contact: [email protected]"
```

## Next Steps

1. **Immediate**: Create OpenStack Foundation account
2. **Short-term**: Submit initial marketplace listing manually  
3. **Long-term**: Automate update notifications

## Contact

- **Marketplace Team**: [email protected]
- **Foundation**: https://www.openstack.org/foundation/
