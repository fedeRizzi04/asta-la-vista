from unittest.mock import Mock

import pytest

from asta_la_vista.entrypoints.flask_app import create_app
from asta_la_vista.service_layer.messagebus import MessageBus


@pytest.fixture
def frontend_client(tmp_path):
    (tmp_path / "index.html").write_text("<h1>Asta la Vista</h1>")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('ready');")

    app = create_app(
        {
            "TESTING": True,
            "API_TITLE": "Test API",
            "API_VERSION": "v1",
            "OPENAPI_VERSION": "3.1.0",
            "FRONTEND_DIST": tmp_path,
        },
        message_bus_factory=lambda: Mock(spec=MessageBus),
    )
    return app.test_client()


def test_serves_frontend_index_and_assets(frontend_client):
    index_response = frontend_client.get("/")
    asset_response = frontend_client.get("/assets/app.js")

    assert index_response.status_code == 200
    assert "Asta la Vista" in index_response.get_data(as_text=True)
    assert asset_response.status_code == 200
    assert "console.log('ready');" in asset_response.get_data(as_text=True)


def test_frontend_routes_fall_back_to_index(frontend_client):
    response = frontend_client.get("/auctions/auction-id")

    assert response.status_code == 200
    assert "Asta la Vista" in response.get_data(as_text=True)


def test_unknown_api_routes_do_not_fall_back_to_frontend(frontend_client):
    response = frontend_client.get("/api/unknown")

    assert response.status_code == 404
    assert "Asta la Vista" not in response.get_data(as_text=True)
