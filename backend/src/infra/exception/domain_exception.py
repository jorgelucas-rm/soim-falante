from src.app.model.enum import HttpCode


class DomainException(Exception):
    """Base para todas as exceções de domínio."""

    http_code: HttpCode

    def __init__(self, message: str, http_code: HttpCode):
        super().__init__(message)
        self.message = message
        self.http_code = http_code
