from typing import Dict

import pulumi


class MyClassProperties:
    """MyClass properties passed to a MyClass instance and used to initialize and configure it."""

    def __init__(self):
        """Initializes MyClassProperties using the given parameters."""
        pass

    @classmethod
    def from_config(cls, cfg: Dict[str, str]):
        """Returns a MyClassProperties instance configured using the passed configuration.

        Args:
            cfg: The config retrieved from the stack

        Returns:
            An instance of MyClassProperties configured using the passed configuration.
        """
        return MyClassProperties()


class MyClass(pulumi.ComponentResource):
    """Represents a deployment of myclass."""

    def __init__(self, name: str, props: MyClassProperties, opts=None):
        """Initializes MyClass using the given parameters."""
        super().__init__('glab:kubernetes:myclass', name, None, opts)