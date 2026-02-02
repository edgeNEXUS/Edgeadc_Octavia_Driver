# VIP Creation Testing Notes

## Test Device: 192.168.3.159 (AutoDeployment-Rocky-3.159)

### Issue Observed
The EdgeADC API returns `success: true` and `StatusText: "Your changes have been applied"` for VIP creation requests, but the VIP is not actually created.

### Tests Performed
1. **Minimal payload** - ipAddr, port, subnetMask, serviceType
2. **Full payload** - All fields matching existing VIPs
3. **Form-encoded data** - Returns "Invalid details in request"
4. **With InterfaceID** - Returns success but no VIP created
5. **With sId** - Returns success but no VIP created
6. **New port on existing IP** - Returns success but no VIP created
7. **Different iAction values** - All return success but no VIP created

### Possible Causes
1. **AutoDeployment Mode** - Device name suggests it was deployed via automation and may have restrictions
2. **Cluster Configuration** - Device shows `clusterState: 1` indicating it's in a cluster
3. **Read-only Configuration** - The device may be configured to not accept new VIPs via API

### What Works
- ✓ Authentication (login)
- ✓ Listing VIPs
- ✓ Getting VIP details
- ✓ Adding members to existing VIPs
- ✓ Updating member weights
- ✓ Deleting members
- ✓ Applying configuration

### Recommendation
Test VIP creation on a different EdgeADC device that:
1. Is not in AutoDeployment mode
2. Is not part of a cluster (or is the primary)
3. Has confirmed ability to create VIPs via GUI

The driver code for VIP creation follows the same pattern as the working Autotest2 client and should work on a properly configured device.
