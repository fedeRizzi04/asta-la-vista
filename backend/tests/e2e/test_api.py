import io

import pytest

from asta_la_vista import bootstrap
from asta_la_vista.entrypoints.flask_app import create_app
from asta_la_vista.service_layer.unit_of_work import SqlAlchemyUnitOfWork


@pytest.fixture
def client(session_factory):
    message_bus = bootstrap.bootstrap(SqlAlchemyUnitOfWork(session_factory))
    app = create_app(
        {
            "TESTING": True,
            "API_TITLE": "Test API",
            "API_VERSION": "v1",
            "OPENAPI_VERSION": "3.1.0",
            "OPENAPI_URL_PREFIX": "/api/docs",
        },
        message_bus,
    )
    return app.test_client()


def test_player_import_and_strategy_flow(client):
    response = client.post(
        "/api/players/import",
        data={
            "file": (
                io.BytesIO(b"Id,R,Nome,Squadra\n5841,P,Svilar,Roma\n2764,A,Martinez L.,Inter"),
                "players.csv",
            )
        },
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "added": 2,
        "updated": 0,
        "deactivated": 0,
        "role_changes": 0,
    }
    assert client.get("/api/players?role=A").get_json() == [
        {"id": "2764", "name": "Martinez L.", "team": "Inter", "role": "A", "active": True}
    ]

    strategy_id = client.post("/api/strategies", json={"name": "Principale"}).get_json()["id"]
    tier_id = client.post(
        f"/api/strategies/{strategy_id}/tiers",
        json={"role": "A", "name": "Prima fascia", "color": "#ef4444"},
    ).get_json()["id"]
    response = client.put(
        f"/api/strategies/{strategy_id}/players/2764",
        json={"tier_id": tier_id, "note": "Obiettivo principale"},
    )
    assert response.status_code == 204

    strategy = client.get(f"/api/strategies/{strategy_id}").get_json()
    assert strategy["entries"][0]["team"] == "Inter"
    assert strategy["entries"][0]["tier_id"] == tier_id
    assert strategy["entries"][0]["note"] == "Obiettivo principale"

    response = client.post(f"/api/strategies/{strategy_id}/duplicate", json={"name": "Alternativa"})
    assert response.status_code == 201
    duplicate_id = response.get_json()["id"]
    duplicate = client.get(f"/api/strategies/{duplicate_id}").get_json()
    assert duplicate["name"] == "Alternativa"
    assert duplicate["tiers"][0]["name"] == "Prima fascia"
    assert duplicate["entries"][0]["note"] == "Obiettivo principale"


def test_live_auction_purchase_amendment_and_cancellation_flow(client):
    client.post(
        "/api/players/import",
        data={"file": (io.BytesIO(b"Id,R,Nome,Squadra\n5841,P,Svilar,Roma"), "players.csv")},
    )
    response = client.post(
        "/api/auctions",
        json={
            "name": "Asta amici",
            "initial_credits": 100,
            "goalkeeper_slots": 1,
            "defender_slots": 2,
            "midfielder_slots": 2,
            "forward_slots": 1,
            "participant_names": ["Alice", "Bob"],
        },
    )
    assert response.status_code == 201
    auction_id = response.get_json()["id"]
    auction = client.get(f"/api/auctions/{auction_id}").get_json()
    alice_id, bob_id = [participant["id"] for participant in auction["participants"]]
    assert client.post(f"/api/auctions/{auction_id}/start").status_code == 204

    response = client.post(
        f"/api/auctions/{auction_id}/purchases",
        json={"player_id": "5841", "participant_id": alice_id, "price": 20},
    )
    assert response.status_code == 201
    purchase_id = response.get_json()["id"]
    auction = client.get(f"/api/auctions/{auction_id}").get_json()
    assert auction["participants"][0]["credits_remaining"] == 80
    assert auction["participants"][0]["purchases"][0]["team"] == "Roma"

    response = client.patch(
        f"/api/auctions/{auction_id}/purchases/{purchase_id}",
        json={"participant_id": bob_id, "price": 25},
    )
    assert response.status_code == 204
    auction = client.get(f"/api/auctions/{auction_id}").get_json()
    assert auction["participants"][0]["credits_remaining"] == 100
    assert auction["participants"][1]["credits_remaining"] == 75

    assert client.delete(f"/api/auctions/{auction_id}/purchases/{purchase_id}").status_code == 204
    auction = client.get(f"/api/auctions/{auction_id}").get_json()
    assert auction["purchased_player_ids"] == []
    assert auction["participants"][1]["credits_remaining"] == 100


def test_live_import_requires_confirmation(client):
    first_file = {"file": (io.BytesIO(b"Id,R,Nome,Squadra\n5841,P,Svilar,Roma"), "players.csv")}
    client.post("/api/players/import", data=first_file)
    auction_id = client.post(
        "/api/auctions",
        json={
            "name": "Asta amici",
            "initial_credits": 10,
            "goalkeeper_slots": 1,
            "defender_slots": 0,
            "midfielder_slots": 0,
            "forward_slots": 0,
            "participant_names": ["Alice"],
        },
    ).get_json()["id"]
    client.post(f"/api/auctions/{auction_id}/start")
    second_file = {"file": (io.BytesIO(b"Id,R,Nome,Squadra\n5841,P,Svilar,Roma"), "players.csv")}

    response = client.post("/api/players/import", data=second_file)

    assert response.status_code == 409
    assert response.get_json()["code"] == "confirmation_required"


def test_openapi_contract_exposes_the_main_resources(client):
    response = client.get("/api/docs/openapi.json")

    assert response.status_code == 200
    paths = response.get_json()["paths"]
    assert "/api/players" in paths
    assert "/api/strategies/{strategy_id}" in paths
    assert "/api/auctions/{auction_id}/purchases" in paths
