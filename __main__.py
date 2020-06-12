import storage.nfs as nfs
import pulumi
from pulumi_kubernetes.apps.v1 import Deployment

# Storage
nfs_config = pulumi.Config().require_object('nfs')
nfs_provisioner = nfs.NFSProvisioner("nfs-provisioner", nfs.NFSProperties.from_config(nfs_config))