from typing import Dict

import pulumi
from pulumi_kubernetes.core.v1 import Namespace
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts


class NFSProperties:
    """NFS properties passed to an NFSProvisioner instance and used to initialize and configure it."""

    def __init__(self, server: str, path: str):
        """Initializes NFSProperties using the given parameters.

        Args:
            server: The hostname or IP address of the NFS server
            path: The root NFS path to use for creating mounts
        """
        self.server = server
        self.path = path

    @classmethod
    def from_config(cls, cfg: Dict[str, str]):
        """Returns a NFSProperties instance configured using the passed configuration.

        Args:
            cfg: The config retrieved from the stack

        Returns:
            An instance of NFSProperties configured using the passed configuration.
        """
        return NFSProperties(
            server=cfg['server'],
            path=cfg['path'],
        )


class NFSProvisioner(pulumi.ComponentResource):
    """Represents a deployment of nfs-client-provisioner."""

    def __init__(self, name: str, props: NFSProperties, opts=None):
        """Initializes NFSProvisioner using the given parameters."""
        super().__init__('glab:kubernetes:nfs', name, None, opts)
        self.props = props
        self.namespace = Namespace("nfs-namespace",
                                   metadata={
                                       "name": "nfs"
                                   },
                                   opts=pulumi.ResourceOptions(parent=self))

        self.chart = Chart('nfs-chart', ChartOpts(
            repo='stable',
            chart='nfs-client-provisioner',
            namespace="nfs",
            values={
                'nfs': {
                    'server': props.server,
                    'path': props.path
                },
                "replicaCount": 3,
                "storageClass": {
                    "name": "nfs"
                }
            }
        ),
                           opts=pulumi.ResourceOptions(parent=self))
