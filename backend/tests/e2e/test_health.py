from unittest.mock import Mock

from asta_la_vista.entrypoints.flask_app import bus, create_app
from asta_la_vista.service_layer.messagebus import MessageBus


def test_health_endpoint_returns_ok():
    app = create_app(
        {
            "TESTING": True,
            "API_TITLE": "Test API",
            "API_VERSION": "v1",
            "OPENAPI_VERSION": "3.1.0",
        },
        message_bus_factory=lambda: Mock(spec=MessageBus),
    )

    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_message_bus_is_scoped_to_a_request():
    first_bus = Mock(spec=MessageBus)
    second_bus = Mock(spec=MessageBus)
    message_bus_factory = Mock(side_effect=[first_bus, second_bus])
    app = create_app(
        {
            "TESTING": True,
            "API_TITLE": "Test API",
            "API_VERSION": "v1",
            "OPENAPI_VERSION": "3.1.0",
        },
        message_bus_factory=message_bus_factory,
    )

    with app.test_request_context():
        assert bus() is first_bus
        assert bus() is first_bus

    with app.test_request_context():
        assert bus() is second_bus

    assert message_bus_factory.call_count == 2
