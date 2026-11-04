"""mra-flow installer: installs and updates the payload in an orchestrator repo."""


class InstallError(Exception):
    """A refusal or failure the user must fix; the message says how."""
