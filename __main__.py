import storage.nfs as nfs
from network import cert, metallb, nginx
import pulumi
from pulumi_kubernetes.apps.v1 import Deployment

# Run the base stack
if 'base' in pulumi.get_stack():
    # Storage
    nfs_config = pulumi.Config().require_object('nfs')
    nfs_provisioner = nfs.NFSProvisioner("nfs-provisioner", nfs.NFSProperties.from_config(nfs_config))

    # Network
    lb_config = pulumi.Config().require_object('loadbalancer')
    metallb = metallb.MetalLB("loadbalancer", metallb.MetalLBProperties.from_config(lb_config))

    cert_config = pulumi.Config().require_object('certs')
    certs = cert.CertManager('cert-manager', cert.CertManagerProperties.from_config(cert_config))

# Run the web stack
if 'web' in pulumi.get_stack():
    vault_addr = pulumi.Config().require('vault_address')

    issuer_config = pulumi.Config().require_object('issuer')
    issuer = cert.ClusterIssuer('cluster-issuer', cert.ClusterIssuerProperties.from_config(issuer_config), vault_addr)

    nginx_config = pulumi.Config().require_object('nginx')
    nginx = nginx.NGINX('nginx', nginx.NGINXProperties.from_config(nginx_config))