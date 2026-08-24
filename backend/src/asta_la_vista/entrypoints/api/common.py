from flask import Flask

from asta_la_vista.exceptions import ConfirmationRequiredError, NotFoundError, ValidationError


def register_error_handlers(app: Flask):
    @app.errorhandler(NotFoundError)
    def handle_not_found(error):
        return {"code": "not_found", "message": str(error)}, 404

    @app.errorhandler(ConfirmationRequiredError)
    def handle_confirmation_required(error):
        return {"code": "confirmation_required", "message": str(error)}, 409

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return {"code": "validation_error", "message": str(error)}, 422
