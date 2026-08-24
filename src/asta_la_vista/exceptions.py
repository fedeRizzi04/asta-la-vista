class ApplicationError(Exception):
    """Base class for expected application errors."""


class ValidationError(ApplicationError):
    """Raised when a command would violate a domain rule."""


class NotFoundError(ApplicationError):
    """Raised when a requested resource does not exist."""
