from typing import Dict

import pulumi
from pulumi_kubernetes.apiextensions import CustomResource
from pulumi_kubernetes.core.v1 import Namespace
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts


class NGINXProperties:
    """NGINX properties passed to a NGINX instance and used to initialize and configure it."""

    def __init__(self, namespace: str):
        """Initializes NGINXProperties using the given parameters."""
        self.namespace_str = namespace

    @classmethod
    def from_config(cls, cfg: Dict[str, str]):
        """Returns a NGINXProperties instance configured using the passed configuration.

        Args:
            cfg: The config retrieved from the stack

        Returns:
            An instance of NGINXProperties configured using the passed configuration.
        """
        return NGINXProperties(
            namespace=cfg['namespace'],
        )


class NGINX(pulumi.ComponentResource):
    """Represents a deployment of NGINX."""

    def __init__(self, name: str, props: NGINXProperties, opts=None):
        """Initializes NGINX using the given parameters."""
        super().__init__('glab:kubernetes:NGINX', name, None, opts)
        self.props = props
        self.namespace = Namespace('nginx-namespace',
                                   metadata={
                                       "name": self.props.namespace_str
                                   },
                                   opts=pulumi.ResourceOptions(parent=self))
        self.chart = Chart('nginx-chart', ChartOpts(
            fetch_opts=FetchOpts(
                repo='https://helm.nginx.com/stable',
            ),
            chart='nginx-ingress',
            namespace=self.props.namespace_str,
            values={
                'controller': {
                    'wildcardTLS': {
                        'secret': '{}/{}'.format(self.props.namespace_str, 'gilmanio-wildcard-cert-secret')
                    }
                }
            }
        ),
                           opts=pulumi.ResourceOptions(parent=self, depends_on=[self.namespace]))
        self.widlcard_cert = CustomResource('nginx-wildcard-cert',
                                            api_version='cert-manager.io/v1alpha2',
                                            kind='Certificate',
                                            metadata={
                                                'name': 'gilmanio-wildcard-cert',
                                                'namespace': self.props.namespace_str,
                                            },
                                            spec={
                                                'secretName': 'gilmanio-wildcard-cert-secret',
                                                'issuerRef': {
                                                    'name': 'letsencrypt',
                                                    'kind': 'ClusterIssuer'
                                                },
                                                'commonName': '*.gilman.io',
                                                'dnsNames': [
                                                    'gilman.io',
                                                    '*.gilman.io',
                                                ],
                                            },
                                            opts=pulumi.ResourceOptions(parent=self))
