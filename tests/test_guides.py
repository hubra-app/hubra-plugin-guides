"""The guides plugin: one usage guide per inventory item.

Items are made through Inventory's API, not its code: Guides only knows
Inventory through its contracts.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from hubra_guides.models import ItemGuide


@pytest.fixture
def item(client, auth_headers, db, seeded_db):
    resp = client.post(
        "/api/v1/inventory/",
        json={"name": "Laser cutter", "category": "Tool", "status": "available"},
    )
    assert resp.status_code == 201, resp.get_json()
    return SimpleNamespace(id=resp.get_json()["id"])


def test_save_and_read_guide(client, auth_headers, item):
    resp = client.put(
        f"/api/v1/guides/{item.id}",
        json={
            "guide": "# Safety\nWear goggles.",
            "guide_url": "https://drive.google.com/x",
        },
    )
    assert resp.status_code == 200
    got = client.get(f"/api/v1/guides/{item.id}").get_json()
    assert got["guide"].startswith("# Safety")
    assert got["guideUrl"] == "https://drive.google.com/x"
    assert [g["itemId"] for g in client.get("/api/v1/guides/").get_json()] == [item.id]


def test_guide_url_must_be_https(client, auth_headers, item):
    resp = client.put(f"/api/v1/guides/{item.id}", json={"guide_url": "http://x"})
    assert resp.status_code == 400


def test_item_api_does_not_leak_guide(client, auth_headers, item, db):
    db.session.add(ItemGuide(item_id=item.id, guide="secret steps"))
    db.session.commit()
    body = client.get(f"/api/v1/inventory/{item.id}").get_json()
    assert "guide" not in str(body.keys())


def test_guide_url_length_is_checked(client, auth_headers, item):
    url = "https://example.org/" + "a" * 500
    resp = client.put(f"/api/v1/guides/{item.id}", json={"guide_url": url})
    assert resp.status_code == 400


def test_deleted_item_has_no_guide(client, auth_headers, item, db):
    client.put(f"/api/v1/guides/{item.id}", json={"guide": "steps"})
    assert client.delete(f"/api/v1/inventory/{item.id}").status_code in (200, 204)
    assert client.get(f"/api/v1/guides/{item.id}").status_code == 404
    resp = client.put(f"/api/v1/guides/{item.id}", json={"guide": "x"})
    assert resp.status_code == 404


def test_a_deleted_items_guide_goes_with_it(client, auth_headers, item, db):
    from hubra_guides.hooks import on_item_deleted

    client.put(f"/api/v1/guides/{item.id}", json={"guide": "steps"})
    on_item_deleted(None, item_id=item.id)
    db.session.commit()
    assert db.session.get(ItemGuide, item.id) is None


def test_an_unknown_item_has_no_guide(client, auth_headers, item):
    assert client.get("/api/v1/guides/99999").status_code == 404
