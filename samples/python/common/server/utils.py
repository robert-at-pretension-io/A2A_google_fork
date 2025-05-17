import os

from common.types import (
    ContentTypeNotSupportedError,
    JSONRPCResponse,
    UnsupportedOperationError,
)


def are_modalities_compatible(
    server_output_modes: list[str], client_output_modes: list[str]
):
    """Modalities are compatible if they are both non-empty
    and there is at least one common element.
    """
    if client_output_modes is None or len(client_output_modes) == 0:
        return True

    if server_output_modes is None or len(server_output_modes) == 0:
        return True

    return any(x in server_output_modes for x in client_output_modes)


def new_incompatible_types_error(request_id):
    return JSONRPCResponse(id=request_id, error=ContentTypeNotSupportedError())


def new_not_implemented_error(request_id):
    return JSONRPCResponse(id=request_id, error=UnsupportedOperationError())


def get_service_hostname(default_host="0.0.0.0"):
    """
    Returns the service hostname to use in agent cards.
    
    When running in Docker/Tilt environments, this will return the service name
    specified by A2A_SERVICE_HOST. Otherwise, it returns the provided default host.
    
    Args:
        default_host: The default hostname to use if A2A_SERVICE_HOST is not set
        
    Returns:
        str: The hostname to use in the agent card URL
    """
    return os.environ.get("A2A_SERVICE_HOST", default_host)
