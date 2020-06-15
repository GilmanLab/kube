from typing import Dict

import pulumi
import hvac
from pulumi_kubernetes import yaml
from pulumi_kubernetes.core.v1 import Namespace, Secret
from pulumi_kubernetes.apiextensions import CustomResource
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts
from typing import Any


class ACME:
    """Represents an ACME provider like Let's Encrypt."""

    def __init__(self, address: str, email: str):
        """Initializes ACME using the given parameters.

        Args:
            address: The URL to the ACME API endpoint
            email: The email address for the account to authenticate with
        """
        self.address = address
        self.email = email


class CloudFlare:
    """Represents an API connection to CloudFlare."""

    def __init__(self, email: str, api_path: str, api_key: str):
        """Initializes CloudFlare using the given parameters.

        Args:
            email: The email address for the API account
            api_path: The Vault path to the API token
            api_key: The Vault key for the API token
        """
        self.email = email
        self.api_path = api_path
        self.api_key = api_key


class CertManagerProperties:
    """CertManager properties passed to a CertManager instance and used to initialize and configure it."""

    def __init__(self, namespace: str):
        """Initializes CertManagerProperties using the given parameters.

        Args:
            acme: Instance of a configured ACME
            cloudflare: Instance of a configured CloudFlare
        """
        self.namespace_str = namespace

    @classmethod
    def from_config(cls, cfg: Dict[str, Any]):
        """Returns a CertManagerProperties instance configured using the passed configuration.

        Args:
            cfg: The config retrieved from the stack

        Returns:
            An instance of CertManagerProperties configured using the passed configuration.
        """
        return CertManagerProperties(
            namespace=cfg['namespace'],
        )


class ClusterIssuerProperties:
    """ClusterIssuer properties passed to a ClusterIssuer instance and used to initialize and configure it."""

    def __init__(self, namespace: str, acme: ACME, cloudflare: CloudFlare):
        """Initializes ClusterIssuerProperties using the given parameters.

            Args:
                acme: Instance of a configured ACME
                cloudflare: Instance of a configured CloudFlare
        """
        self.namespace_str = namespace
        self.acme = acme
        self.cloudflare = cloudflare

    @classmethod
    def from_config(cls, cfg: Dict[str, Any]):
        """Returns a CertManagerProperties instance configured using the passed configuration.

        Args:
            cfg: The config retrieved from the stack

        Returns:
            An instance of CertManagerProperties configured using the passed configuration.
        """
        return ClusterIssuerProperties(
            namespace=cfg['namespace'],
            acme=ACME(
                address=cfg['acme']['address'],
                email=cfg['acme']['email'],
            ),
            cloudflare=CloudFlare(
                email=cfg['cloudflare']['email'],
                api_path=cfg['cloudflare']['api_token']['path'],
                api_key=cfg['cloudflare']['api_token']['key'],
            ),
        )


class CertManager(pulumi.ComponentResource):
    """Represents a deployment of cert-manager."""

    def __init__(self, name: str, props: CertManagerProperties, opts=None):
        """Initializes CertManager using the given parameters.

        Args:
            name: Name of the resource
            props: Instance of CertManagerProperties to configure with
            opts: An optional set of ResourceOptions to configure this node with
        """
        super().__init__('glab:kubernetes:CertManager', name, None, opts)
        self.props = props

        self.namespace = Namespace('cert-manager-namespace',
                                   metadata={
                                       "name": self.props.namespace_str
                                   },
                                   opts=pulumi.ResourceOptions(parent=self))
        self.chart = Chart('cert-manager-chart', ChartOpts(
            fetch_opts=FetchOpts(
                repo='https://charts.jetstack.io',
            ),
            chart='cert-manager',
            namespace=self.props.namespace_str,
            values={
                "installCRDs": True,
            }
        ),
                           opts=pulumi.ResourceOptions(parent=self, depends_on=[self.namespace]))


class ClusterIssuer(pulumi.ComponentResource):
    """Represents a ClusterIssuer custom resource."""

    def __init__(self, name: str, props: ClusterIssuerProperties, vault_addr: str, opts=None):
        """Initializes ClusterIssuer using the given parameters.

        Args:
            name: Name of the resource
            props: Instance of ClusterIssuerProperties to configure with
            vault_addr: URL address of the Vault server for fetching API token
            opts: An optional set of ResourceOptions to configure this node with
        """
        super().__init__('glab:kubernetes:ClusterIssuer', name, None, opts)
        self.props = props

        # Vault secret
        client = hvac.Client(url=vault_addr)
        data = client.secrets.kv.v1.read_secret(path=self.props.cloudflare.api_path, mount_point='secret')
        token = data['data'][self.props.cloudflare.api_key]

        self.token_secret = Secret('cert-manager-privkey-secret',
                                   metadata={
                                       'namespace': self.props.namespace_str,
                                       'name': 'cloudflare-api-token-secret'
                                   },
                                   string_data={
                                       'api-token': token,
                                   },
                                   opts=pulumi.ResourceOptions(parent=self))
        self.issuer = CustomResource('cert-manager-issuer',
                                     api_version='cert-manager.io/v1alpha2',
                                     kind='ClusterIssuer',
                                     metadata={
                                         'name': 'letsencrypt',
                                     },
                                     spec={
                                         'acme': {
                                             'email': self.props.acme.email,
                                             'server': self.props.acme.address,
                                             'privateKeySecretRef': {
                                                 'name': 'le-account-key'
                                             },
                                             'solvers': [
                                                 {
                                                     'dns01': {
                                                         'cloudflare': {
                                                             'email': self.props.cloudflare.email,
                                                             'apiTokenSecretRef': {
                                                                 'name': 'cloudflare-api-token-secret',
                                                                 'key': 'api-token',
                                                             }
                                                         }
                                                     }
                                                 }
                                             ],
                                         }
                                     },
                                     opts=pulumi.ResourceOptions(parent=self,
                                                                 depends_on=[self.token_secret]))
