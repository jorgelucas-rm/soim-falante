from src.app.model.enum import HttpCode
from src.infra.exception.domain_exception import DomainException


class UnauthorizedException(DomainException):
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message=message, http_code=HttpCode.UNAUTHORIZED)


class ForbiddenException(DomainException):
    def __init__(self, message: str = "You do not have permission to access this resource"):
        super().__init__(message=message, http_code=HttpCode.FORBIDDEN)


class NotFoundException(DomainException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(message=f"{resource} not found", http_code=HttpCode.NOT_FOUND)


class ConflictException(DomainException):
    def __init__(self, message: str = "Conflict detected"):
        super().__init__(message=message, http_code=HttpCode.CONFLICT)


class BadRequestException(DomainException):
    def __init__(self, error_type: str, details: str = ""):
        message = f"Error in requisition: {error_type}"
        if details:
            message = f"{message} - {details}"
        super().__init__(message=message, http_code=HttpCode.UNPROCESSABLE_ENTITY)


class EnvironmentException(DomainException):
    def __init__(self, key: str):
        super().__init__(
            message=f"Required environment variable not defined: {key}",
            http_code=HttpCode.INTERNAL_SERVER_ERROR,
        )


class StorageException(DomainException):
    def __init__(self, message: str = "Storage operation failed"):
        super().__init__(message=message, http_code=HttpCode.INTERNAL_SERVER_ERROR)
