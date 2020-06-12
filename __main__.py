import storage.nfs as nfs
import network.metallb as lb
import pulumi
from pulumi_kubernetes.apps.v1 import Deployment

# Storage
nfs_config = pulumi.Config().require_object('nfs')
nfs_provisioner = nfs.NFSProvisioner("nfs-provisioner", nfs.NFSProperties.from_config(nfs_config))

# Network
lb_config = pulumi.Config().require_object('loadbalancer')
metallb = lb.MetalLB("loadbalancer", lb.MetalLBProperties.from_config(lb_config))