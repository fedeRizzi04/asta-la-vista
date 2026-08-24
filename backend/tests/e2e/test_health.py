from unittest.mock import Mock

from asta_la_vista.entrypoints.flask_app import create_app
from asta_la_vista.service_layer.messagebus import MessageBus


def test_health_endpoint_returns_ok():
    app = create_app(
        {
            "TESTING": True,
            "API_TITLE": "Test API",
            "API_VERSION": "v1",
            "OPENAPI_VERSION": "3.1.0",
        },
        message_bus=Mock(spec=MessageBus),
    )

    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
