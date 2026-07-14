class AppError(Exception):
    """Base application error mapped to an HTTP response."""

    status_code = 500
    default_message = "Internal server error"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    default_message = "Resource not found"


class UnauthorizedError(AppError):
    status_code = 401
    default_message = "Not authenticated"


class ForbiddenError(AppError):
    status_code = 403
    default_message = "Not allowed"


class ConflictError(AppError):
    status_code = 409
    default_message = "Conflict"


class DomainValidationError(AppError):
    status_code = 422
    default_message = "Validation error"
