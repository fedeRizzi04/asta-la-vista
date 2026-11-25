from flask import Flask

from asta_la_vista.exceptions import ConfirmationRequiredError, NotFoundError, ValidationError


def register_error_handlers(app: Flask):
    @app.errorhandler(NotFoundError)
    def handle_not_found(error):
        return {"code": error.code, "params": error.params}, 404

    @app.errorhandler(ConfirmationRequiredError)
    def handle_confirmation_required(error):
        return {"code": error.code, "params": error.params}, 409

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return {"code": error.code, "params": error.params}, 422
