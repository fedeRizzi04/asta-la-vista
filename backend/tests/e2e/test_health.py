from unittest.mock import Mock

import pytest

from asta_la_vista.adapters.releases import Release, ReleaseChecker
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


def test_version_endpoint_returns_installed_package_version():
    from importlib.metadata import version

    app = create_app(
        {
            "TESTING": True,
            "API_TITLE": "Test API",
            "API_VERSION": "v1",
            "OPENAPI_VERSION": "3.1.0",
        },
        message_bus_factory=lambda: Mock(spec=MessageBus),
    )

    response = app.test_client().get("/api/version")

    assert response.status_code == 200
    assert response.get_json() == {
        "version": version("asta-la-vista"),
        "latest_version": None,
        "release_url": None,
        "update_available": False,
    }
    assert "release_checker" not in app.extensions  # no update check unless enabled


@pytest.mark.parametrize(
    ("latest", "update_available"),
    [("99.0.0", True), ("0.0.1", False)],
)
def test_version_endpoint_reports_the_latest_release(latest, update_available):
    url = f"https://github.com/fedeRizzi04/asta-la-vista/releases/tag/v{latest}"
    app = create_app(
        {
            "TESTING": True,
            "API_TITLE": "Test API",
            "API_VERSION": "v1",
            "OPENAPI_VERSION": "3.1.0",
            "UPDATE_CHECK": True,
        },
        message_bus_factory=lambda: Mock(spec=MessageBus),
    )
    assert isinstance(app.extensions["release_checker"], ReleaseChecker)
    app.extensions["release_checker"] = ReleaseChecker(fetch=lambda: Release(latest, url))

    body = app.test_client().get("/api/version").get_json()

    assert body["latest_version"] == latest
    assert body["release_url"] == url
    assert body["update_available"] is update_available


def test_version_endpoint_works_offline():
    def offline() -> Release:
        raise OSError("no network")

    app = create_app(
        {
            "TESTING": True,
            "API_TITLE": "Test API",
            "API_VERSION": "v1",
            "OPENAPI_VERSION": "3.1.0",
            "UPDATE_CHECK": True,
        },
        message_bus_factory=lambda: Mock(spec=MessageBus),
    )
    app.extensions["release_checker"] = ReleaseChecker(fetch=offline)

    response = app.test_client().get("/api/version")

    assert response.status_code == 200
    assert response.get_json()["update_available"] is False
