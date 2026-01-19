from rest_framework.response import Response
from rest_framework import status

class ResponseHandler:
    @staticmethod
    def success(message="Success.", data=None, status_code=status.HTTP_200_OK, extra=None):
        payload = {"success": True, "message": message}
        if data is not None:
            payload["data"] = data
        if extra:
            payload["extra"] = extra
        return Response(payload, status=status_code)

    @staticmethod
    def created(message="Created successfully.", data=None, extra=None):
        return ResponseHandler.success(message, data, status.HTTP_201_CREATED, extra)

    @staticmethod
    def updated(message="Updated successfully.", data=None, extra=None):
        return ResponseHandler.success(message, data, status.HTTP_200_OK, extra)

    @staticmethod
    def deleted(message="Deleted successfully.", extra=None):
        payload = {"success": True, "message": message}
        if extra:
            payload["extra"] = extra
        return Response(payload, status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def error(message="An error occurred.", errors=None, status_code=status.HTTP_400_BAD_REQUEST, extra=None):
        payload = {"success": False, "message": message}
        if errors is not None:
            payload["errors"] = errors
        if extra:
            payload["extra"] = extra
        return Response(payload, status=status_code)

    @staticmethod
    def bad_request(message="Invalid request.", errors=None, extra=None):
        return ResponseHandler.error(message, errors, status.HTTP_400_BAD_REQUEST, extra)

    @staticmethod
    def unauthorized(message="Authentication required.", errors=None, extra=None):
        return ResponseHandler.error(message, errors, status.HTTP_401_UNAUTHORIZED, extra)

    @staticmethod
    def forbidden(message="Access forbidden.", errors=None, extra=None):
        return ResponseHandler.error(message, errors, status.HTTP_403_FORBIDDEN, extra)

    @staticmethod
    def not_found(message="Resource not found.", errors=None, extra=None):
        return ResponseHandler.error(message, errors, status.HTTP_404_NOT_FOUND, extra)

    @staticmethod
    def conflict(message="Conflict detected.", errors=None, extra=None):
        return ResponseHandler.error(message, errors, status.HTTP_409_CONFLICT, extra)

    @staticmethod
    def server_error(message="Internal server error.", errors=None, extra=None):
        return ResponseHandler.error(message, errors, status.HTTP_500_INTERNAL_SERVER_ERROR, extra)
