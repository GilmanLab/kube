from typing import Any, Dict

import pulumi
import random
import string
import yaml as yml
from pulumi_kubernetes import yaml
from pulumi_kubernetes.core.v1 import ConfigMap, Namespace, Secret


class MetalLBProperties:
    """MetalLB properties passed to an MetalLB instance and used to initialize and configure it."""

    def __init__(self, manifest: str, namespace: str, network_start: str, network_end: str):
        """Initializes MetalLBProperties using the given parameters.

        Args:
            network_start: The start range of addresses that the LB will assign
            network_end: The end range of addresses that the LB will assign
        """
        self.manifest = manifest
        self.namespace_str = namespace
        self.network_start = network_start
        self.network_end = network_end

    @classmethod
    def from_config(cls, cfg: Dict[str, Any]):
        """Returns a MetalLBProperties instance configured using the passed configuration.

        Args:
            cfg: The config retrieved from the stack

        Returns:
            An instance of MetalLBProperties configured using the passed configuration.
        """
        return MetalLBProperties(
            manifest=cfg['manifest'],
            namespace=cfg['namespace'],
            network_start=cfg['network']['start'],
            network_end=cfg['network']['end'],
        )


class MetalLB(pulumi.ComponentResource):
    """Represents a deployment of MetalLB."""

    def __init__(self, name: str, props: MetalLBProperties, opts=None):
        """Initializes MetalLB using the given parameters."""
        super().__init__('glab:kubernetes:metallb', name, None, opts)
        self.props = props
        self.namespace = Namespace('metallb-namespace',
                                   metadata={
                                       'name': self.props.namespace_str,
                                       'labels': {
                                           'app': 'metallb'
                                       }
                                   },
                                   opts=pulumi.ResourceOptions(parent=self))

        self.resources = yaml.ConfigFile('metallb-resources',
                                         self.props.manifest,
                                         transformations=[self._add_namespace],
                                         opts=pulumi.ResourceOptions(parent=self))

        secret_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(128))
        self.secret = Secret('metallb-memberlist',
                             metadata={
                                 'namespace': self.props.namespace_str,
                                 'name': 'memberlist'
                             },
                             type='general',
                             string_data={
                                 'secretkey': secret_key
                             },
                             opts=pulumi.ResourceOptions(parent=self))

        config = {
            'address-pools': [
                {
                    'name': 'default',
                    'protocol': 'layer2',
                    'addresses': [
                        '{}-{}'.format(props.network_start, props.network_end)
                    ]
                }
            ]
        }
        self.config = ConfigMap('metallb-config',
                                metadata={
                                    'namespace': self.props.namespace_str,
                                    'name': 'config'
                                },
                                data={
                                    "config": yml.dump(config)
                                },
                                opts=pulumi.ResourceOptions(parent=self))

    def _add_namespace(self, obj, opts=None):
        obj['metadata']['namespace'] = self.props.namespace_str

