import logging
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import ValidationError, PermissionDenied, NotAuthenticated, APIException

logger = logging.getLogger(__name__)

def build_response(
    success: bool,
    message: str,
    data=None,
    errors=None,
    status_code=status.HTTP_200_OK,
) -> Response:
    """Minimal response builder."""
    return Response(
        {
            "success": success,
            "message": message,
            "data": data or {},
            "errors": errors or {},
        },
        status=status_code,
    )


# Simple, fast response helpers
def success_response(message="Request successful.", data=None):
    return build_response(True, message, data=data)

def created_response(message="Resource created.", data=None):
    return build_response(True, message, data=data, status_code=status.HTTP_201_CREATED)

def bad_request_response(message="Invalid request.", errors=None):
    return build_response(False, message, errors=errors, status_code=status.HTTP_400_BAD_REQUEST)

def unauthorized_response(message="Authentication required.", errors=None):
    return build_response(False, message, errors=errors, status_code=status.HTTP_401_UNAUTHORIZED)

def forbidden_response(message="Access forbidden.", errors=None):
    return build_response(False, message, errors=errors, status_code=status.HTTP_403_FORBIDDEN)

def server_error_response(message="Internal server error.", errors=None):
    return build_response(False, message, errors=errors, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)